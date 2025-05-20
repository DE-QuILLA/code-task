from redis.asyncio import Redis
from typing import Dict, List, Any, Set
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.data_models.kraken_active_pair_data_models import KrakenActivePairDataModel
from kraken_modules.utils.wrappers.custrom_retry_wrapper import custom_retry


class KrakenRedisClient:
    """
    Redis 인스턴스와의 연결을 나타내는 객체
    """
    def __init__(self, redis_url: str, retry_num: int = 5, retry_delay: int = 2, conn_timeout: int = 10):
        self.redis_url = redis_url
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.conn_timeout = conn_timeout
        self.component = "REDIS CLIENT"
        self.redis: Redis = None
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger("REDIS CLIENT")
        self.is_healthy = False
        self._connect_redis()  # 레디스 실제 연결

    async def _connect_redis(self):
        """Redis로 연결하는 객체 생성하고 ping을 보냄 (반복 시도, ping을 보내는 시점에 실제 Connection이 생김)"""
        try:
            self.logger.info_start(description="Redis 연결")
            self.redis = Redis.from_url(url=self.redis_url, decode_responses=True)
            pong = await self._ping_with_retry(desc_override="Redis 연결 상태 확인")
            if pong:
                self.is_healthy = True
                self.logger.info_success(description="Redis 연결")
            else:
                self.is_healthy = False
                self.logger.warning_common(description="예외 없는 Redis Ping 실패")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis 연결")
            raise e
        finally:
            if self.redis and not self.is_healthy:
                self.logger.warning_common(f"Redis 연결 종료")
                self.close()

    async def _ping_with_retry(self, desc_override=None) -> bool:
        description = desc_override or "[REDIS PING]"
        return await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=description,
            func=self.redis.ping,
            func_kwargs=None,
        )

    def get_status(self):
        """스테이터스 반환"""
        return self.is_healthy

    async def close(self):
        """커넥션 종료"""
        await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description="Redis 연결 종료",
            func=self.redis.close,
            func_kwargs=None,
        )

    async def fetch_all_data(self, redis_key: str):
        """특정 key의 모든 데이터를 가져오는 기능"""
        return await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=f"[{redis_key}] KEY 데이터 GET ALL 요청",
            func=self.redis.smembers,
            func_args=(redis_key,)
        )
    
    async def delete_all_data(self, redis_key: str):
        """특정 key의 모든 데이터를 삭제하는 기능"""
        return await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=f"[{redis_key}] KEY 데이터 DELETE 요청",
            func=self.redis.delete,
            func_args=(redis_key,)
        )
    
    async def save_set_data(self, redis_key: str, new_data_set: Set[str]):
        """특정 key에 데이터를 저장하는 함수"""
        return await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=f"[{redis_key}] KEY 데이터 SAVE 요청",
            func=self.redis.sadd,
            func_args=(redis_key, *new_data_set)
        )

    async def update_if_changed(self, redis_key: str, new_data_set: Set[str]) -> bool:
        """기존 Redis 데이터와 비교 후 변경된 항목만 저장, Pipeline 사용 배치"""
        self.logger.info_start(f"Redis {redis_key} 키 갱신")
        old_data = await self.fetch_all_data(redis_key=redis_key)
        old_data_set = set(old_data)

        if old_data_set != new_data_set:
            self.logger.warning_common("새로운 구독쌍 데이터")
            await self.delete_all_data(redis_key=redis_key)

            if new_data_set:
                await self.save_set_data(redis_key=redis_key, new_data=new_data_set)
            
            self.logger.info_success(f"Redis {redis_key} 키 갱신")
            return True
        else:
            self.logger.warning_common("갱신할 구독쌍 데이터 없음")
            return False

