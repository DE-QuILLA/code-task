from redis.asyncio import Redis
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger, get_start_info_msg, get_success_info_msg, get_exception_msg, get_error_msg, get_warning_msg
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
import logging

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
        self.logger: logging.Logger = get_stdout_logger("REDIS CLIENT")
        self.health_status = KrakenProducerStatusCodeEnum.NOT_STARTED
        self._connect_redis()  # 레디스 실제 연결

    async def _connect_redis(self):
        """Redis로 연결하는 객체 생성하고 ping을 보냄 (반복 시도, ping을 보내는 시점에 실제 Connection이 생김)"""
        try:
            self.redis = Redis.from_url(url=self.redis_url, decode_responses=True)
            pong = await self._ping_with_retry(desc_override="Redis 연결 상태 확인")
            if pong:
                self.health_status = KrakenProducerStatusCodeEnum.STARTED
                self.logger.info(get_success_info_msg(description="Redis 연결"))
            else:
                self.health_status = KrakenProducerStatusCodeEnum.ERROR
                self.logger.warning(get_warning_msg(description="예외 없는 Redis Pong 실패"))
        except Exception as e:
            self.logger.exception(get_error_msg(error=e, description="Redis 연결"))
            raise e

    async def _ping_with_retry(self, desc_override=None) -> bool:
        description = "Redis Ping" or desc_override
        return await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=description,
            func=self.redis.ping,
            func_kwargs=None,
        )

    async def close(self):
        await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description="Redis 연결 종료",
            func=self.redis.close(),
            func_kwargs=None,
        )
