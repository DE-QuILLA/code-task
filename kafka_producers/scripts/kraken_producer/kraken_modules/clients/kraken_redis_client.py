from redis.asyncio import Redis
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.interfaces.kraken_base_component_with_config import KrakenBaseComponentWithConfig
from kraken_modules.interfaces.kraken_base_health_tracked_component import KrakenBaseHealthTrackedComponent
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus, KrakenProducerStatusManager
from kraken_modules.config_models.kraken_redis_client_configs import KrakenRedisClientConfigModel


# redis_url: str = "redis://redis-master.redis.svc.cluster.local:6379/0"
#     retry_num: Optional[int] = 5
#     retry_delay: Optional[int] = 2
#     conn_timeout: Optional[int] = 10
#     component_name: str = "REDIS CLIENT"

class KrakenRedisClient(KrakenBaseComponentWithConfig, KrakenBaseHealthTrackedComponent):
    """
    Redis 인스턴스와의 연결을 나타내는 객체
    """
    def __init__(self, config: KrakenRedisClientConfigModel, status_manager: KrakenProducerStatusManager,):
        # config 객체에서 가져오는 값
        self.redis_url: str = config.redis_url
        self.retry_num: int = config.retry_num
        self.retry_delay: int = config.retry_delay
        self.conn_timeout: int = config.conn_timeout
        self.component_name: str = config.component_name

        # 동적 초기화, 외부 주입 객체
        self.redis: Redis = None
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.component_name,)

    async def initialize_redis_client(self) -> None:
        try:
            self.logger.info_start("Redis Client 초기화")
            await self._connect_redis()
            await self.status_manager.register_component(component_name=self.component_name, new_component=self)
            self.logger.info_success("Redis Client 초기화")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis Client 초기화")
            raise e

    async def _connect_redis(self) -> None:
        """Redis로 연결하는 객체 생성하고 ping을 보냄 (반복 시도, ping을 보내는 시점에 실제 Connection이 생김)"""
        try:
            self.logger.info_start(description="Redis 연결")
            self.redis = Redis.from_url(url=self.redis_url, decode_responses=True)
            pong = await self._ping_with_retry(desc_override="Redis 연결 상태 확인")
            if pong:
                self.logger.info_success(description="Redis 연결")
            else:
                self.logger.warning_common(description="예외 없는 Redis Pong 실패")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis 연결")
            raise e
        

    async def _ping_with_retry(self, desc_override: str = None) -> bool:
        description = desc_override or "Redis Ping"
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
            func=self.redis.hgetall,
            func_kwargs={"name": redis_key}
        )

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        헬스 체크용 메소드
        """
        try:
            self.logger.info_start(description="헬스 체크")
            pong = await self._ping_with_retry(desc_override="헬스 체크 - Redis 연결 상태 확인")
            if pong:
                status = KrakenProducerComponentHealthStatus(component_name=self.component_name,
                                                    component=self, is_healthy=pong,
                                                    health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                                                    last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                                                    message=f"{self.component_name} IS HEALTHY",
                                                    )
                self.logger.info_success(description="헬스 체크")
            else:
                status = KrakenProducerComponentHealthStatus(component_name=self.component_name,
                                                    component=self, is_healthy=False,
                                                    health_status_code=KrakenProducerStatusCodeEnum.CLIENT_FAIL_TO_CONNECT.value,
                                                    last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                                                    message=f"{self.component_name} FAILED HEALTH CHECK",
                                                    )
                self.logger.warning_common(description="헬스 체크 중 예외 없는 Redis Ping 실패")
        except Exception as e:
            self.logger.exception_common(error=e, description="헬스 체크 중 Redis 연결")
            raise e
        return status

    async def update_component_status(self) -> None:
        """
        자신의 status를 업데이트하는 메소드
        """
        self.logger.info_start("REDIS CLIENT 상태 업데이트")
        new_status = await self.check_component_health()
        self.status_manager.update_manager_status(component_name=self.component_name, new_status=new_status)
        self.logger.info_success("REDIS CLIENT 상태 업데이트")

