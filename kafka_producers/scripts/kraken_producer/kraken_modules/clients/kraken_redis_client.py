from redis.asyncio import Redis
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus, KrakenProducerStatusManager
from kraken_modules.config_models.kraken_redis_client_configs import KrakenRedisClientConfigModel


class KrakenRedisClient(KrakenBaseComponent):
    """
    Redis 인스턴스와의 연결을 나타내는 객체
    """
    def __init__(self, config: KrakenRedisClientConfigModel, status_manager: KrakenProducerStatusManager,):
        # config 객체 저장
        self.config: KrakenRedisClientConfigModel = config

        # 동적 초기화, 외부 주입 객체
        self.redis: Redis = None
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.component_name,)

    async def initialize_redis_client(self) -> None:
        """
        Redis 인스턴스 초기화
        - 연결 설정
        - 상태 매니저에 등록
        """
        try:
            self.logger.info_start("Redis Client 초기화")
            await self._connect_redis()
            await self.status_manager.register_component(component_name=self.config.component_name, new_component=self)
            self.logger.info_success("Redis Client 초기화")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis Client 초기화")
            raise e

    async def _connect_redis(self) -> None:
        """
        Redis로 연결하는 객체 생성하고 ping 을 보내서 확인함
        - ping을 보내는 시점에 실제 연결 생성됨
        """
        try:
            self.logger.info_start(description="Redis 연결")
            self.redis = Redis.from_url(url=self.config.redis_url, decode_responses=True)
            pong = await self._ping_with_retry(desc_override="Redis 연결 상태 확인")
            if pong:
                self.logger.info_success(description="Redis 연결")
            else:
                self.logger.warning_common(description="예외 없는 Redis Pong 실패")
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis 연결")
            raise e
        

    async def _ping_with_retry(self, desc_override: str = None) -> bool:
        """
        retry 로직을 붙힌 ping 실행
        """
        description = desc_override or "Redis Ping"
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=description,
            func=self.redis.ping,
        )

    async def close(self):
        """
        retry 로직을 붙힌 close 수행
        """
        await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description="Redis 연결 종료",
            func=self.redis.close,
        )

    async def fetch_all_data(self, redis_key: str):
        """
        특정 key의 모든 데이터를 가져오는 기능
        """
        return await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{redis_key}] KEY 데이터 GET ALL 요청",
            func=self.redis.smembers,
            func_args=(redis_key,)
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
