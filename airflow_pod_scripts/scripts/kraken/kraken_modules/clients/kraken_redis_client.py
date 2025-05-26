# libraries
from redis.asyncio import Redis
from typing import Set, Dict, Any, List
import json

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

    async def get_set_members(self, redis_key: str):
        """
        특정 key의 SET 내 모든 멤버를 가져오는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 GET ALL 요청",
            func=self.redis.smembers,
            func_args=(redis_key,),
        )

    async def delete_key(self, redis_key: str):
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

    async def add_set_members(self, redis_key: str, new_data_set: Set[str]):
        """
        특정 key의 SET에 새로운 원소를 추가하는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 SAVE 요청",
            func=self.redis.sadd,
            func_args=(redis_key, *new_data_set),
        )

    async def replace_set_if_changed(self, redis_key: str, new_data_set: Set[str]) -> bool:
        """
        기존 Redis 키의 SET을 가져와 현재 데이터와 비교하고 변화가 있을 시 저장
        - 갱신 시 True, 갱신하지 않을 시 False 반환
        """
        self.logger.info_start(f"Redis {redis_key} 키 갱신")
        old_data = await self.get_set_members(redis_key=redis_key)
        old_data_set = set(old_data)

        if old_data_set != new_data_set:
            self.logger.warning_common(f"[{redis_key}] 내용 변경 감지 → 갱신 수행")
            await self.delete_key(redis_key=redis_key)

            if new_data_set:
                await self.add_set_members(redis_key=redis_key, new_data=new_data_set)

            self.logger.info_success(f"Redis {redis_key} 키 갱신")
            # 변경 발생
            return True
        else:
            self.logger.warning_common("갱신할 구독쌍 데이터 없음")
            # 변경되지 않음
            return False

    async def replace_json_if_changed(self, redis_key: str, new_data: Dict[str, Any]) -> bool:
        """
        기존 Redis JSON 데이터와 비교 후 변경된 항목만 저장하는 기능
        - 여기만 따로 구현 이유: JSON으로 그대로 메타 데이터만 간단히 저장하기 때문
        """
        self.logger.info_start(f"[{redis_key}] (JSON) 키 갱신")
        old_data_raw = self.get_with_retry(redis_key=redis_key,)
        old_data = json.loads(old_data_raw) if old_data_raw else {}

        if old_data != new_data:
            self.logger.warning_common(f"[{redis_key}] 내용 변경 감지 → 갱신 수행")
            json_str = json.dumps(new_data)
            self.set_with_retry(redis_key=redis_key, json_str=json_str)
            self.logger.info_success(f"[{redis_key}] JSON 갱신 완료")
            return True
        else:
            self.logger.info_success(f"[{redis_key}] 내용 동일 → 저장 생략")
            return False

    async def get_with_retry(self, redis_key: str,):
        """
        Redis 키에 저장된 string을 가져오는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"Redis {redis_key} 키 JSON 데이터 GET",
            func=self.redis.get,
            func_args=(redis_key,)
        )
    
    async def set_with_retry(self, redis_key: str, json_str: str):
        """
        Redis 키에 저장된 string을 바꾸는 기능
        """
        return await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=f"Redis {redis_key} 키 JSON 데이터 갱신",
                func=self.redis.set,
                func_args=(redis_key, json_str)
            )

    async def update_intersection_set(
        self,
        redis_keys: List[str],
        dest_key: str
    ) -> bool:
        """
        여러 Set 키들의 교집합을 계산하여 dest_key에 저장.
        변경이 발생했을 경우 True 리턴
        """
        self.logger.info_start(f"[{dest_key}] 교집합 키 갱신 요청")
        try:
            new_data_set = await self.redis.sinter(*redis_keys)
            return await self.replace_set_if_changed(dest_key, set(new_data_set))
        except Exception as e:
            self.logger.exception_common(error=e, description=f"{dest_key} 갱신 중 예외")
            raise
