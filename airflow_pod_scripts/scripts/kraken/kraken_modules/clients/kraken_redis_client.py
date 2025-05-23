# libraries
from redis.asyncio import Redis
from typing import Set

# custom
from kraken_modules.config_models import KrakenRedisClientConfigModel
from kraken_modules.utils.logging import KrakenStdandardLogger
from kraken_modules.utils.wrappers import custom_retry
from kraken_modules.utils.exceptions import (
    KrakenRedisClientConnectionException,
    KrakenRedisClientCanNotCloseException,
)


class KrakenRedisClient:
    """
    Redis 인스턴스와의 연결을 나타내는 객체
    """

    def __init__(self, config: KrakenRedisClientConfigModel):
        # config 객체
        self.config = config

        # 동적 변수 / 외부 객체 주입
        self.is_healthy = False
        self.redis: Redis = None
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(
            self.config.component_name
        )

    async def initialize_redis(
        self,
    ):
        """
        Redis Client 초기화
        """
        self.logger.info_start(f"{self.config.component_name} 초기화")
        await self._connect_redis()
        self.logger.info_success(f"{self.config.component_name} 초기화")

    async def _connect_redis(self):
        """
        Redis로 연결하는 객체 생성하고 ping을 보냄 (반복 시도, ping을 보내는 시점에 실제 Connection이 생김)
        """
        try:
            self.logger.info_start(description="Redis 연결")
            self.redis = Redis.from_url(
                url=self.config.redis_url, decode_responses=True
            )
            pong = await self._ping_with_retry(desc_override="Redis 연결 상태 확인")
            if pong:
                self.is_healthy = True
                self.logger.info_success(description="Redis 연결")
            else:
                self.is_healthy = False
                self.logger.warning_common(description="예외 없는 Redis Ping 실패")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis 연결")
            raise KrakenRedisClientConnectionException(
                "Redis Client 초기화 중 연결 실패"
            )
        finally:
            if self.redis and not self.is_healthy:
                self.logger.warning_common(f"비정상적 Redis 연결 종료")
                self.close()

    async def _ping_with_retry(
        self,
    ) -> bool:
        """
        retry 로직을 포함한 ping to redis
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description="[REDIS PING]",
            func=self.redis.ping,
            func_kwargs=None,
        )

    async def close(self):
        """
        retry 로직을 포함한 커넥션 종료
        """
        try:
            await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=f"[{self.config.redis_url}] 연결 종료",
                func=self.redis.close,
                func_kwargs=None,
            )
        except Exception as e:
            self.logger.exception_common("Redis 연결 종료")
            raise KrakenRedisClientCanNotCloseException

    async def fetch_all_data(self, redis_key: str):
        """
        특정 key의 모든 데이터를 가져오는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 GET ALL 요청",
            func=self.redis.smembers,
            func_args=(redis_key,),
        )

    async def delete_all_data(self, redis_key: str):
        """
        특정 key의 모든 데이터를 삭제하는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 DELETE 요청",
            func=self.redis.delete,
            func_args=(redis_key,),
        )

    async def save_set_data(self, redis_key: str, new_data_set: Set[str]):
        """
        특정 key에 Set 형태의 데이터를 저장하는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 SAVE 요청",
            func=self.redis.sadd,
            func_args=(redis_key, *new_data_set),
        )

    async def update_if_changed(self, redis_key: str, new_data_set: Set[str]) -> bool:
        """
        기존 Redis 데이터와 비교 후 변경된 항목만 저장하는 기능
        """
        self.logger.info_start(f"Redis {redis_key} 키 갱신")
        old_data = await self.fetch_all_data(redis_key=redis_key)
        old_data_set = set(old_data)

        if old_data_set != new_data_set:
            self.logger.warning_common("새로운 구독쌍 데이터")
            await self.delete_all_data(redis_key=redis_key)

            if new_data_set:
                await self.save_set_data(redis_key=redis_key, new_data=new_data_set)

            self.logger.info_success(f"Redis {redis_key} 키 갱신")
            # 변경 발생
            return True
        else:
            self.logger.warning_common("갱신할 구독쌍 데이터 없음")
            # 변경되지 않음
            return False
