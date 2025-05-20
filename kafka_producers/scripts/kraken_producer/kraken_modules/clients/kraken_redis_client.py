# custom
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.managers import KrakenProducerStatusManager
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.config_models import KrakenRedisClientConfigModel
from kraken_modules.utils.wrapper import custom_retry
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum
from kraken_modules.utils.exceptions import KrakenProdcuerRedisConnectionException, KrakenProdcuerRedisCloseFailureException, KrakenProdcuerRedisFetchDataException

# libraries
from redis.asyncio import Redis
from datetime import datetime
from zoneinfo import ZoneInfo


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
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.config.component_name,)

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
            # NOTE: 내부 발생 예외 그대로 raise
            raise

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
            raise
        

    async def _ping_with_retry(self, desc_override: str = None) -> bool:
        """
        retry 로직을 붙힌 ping 실행
        """
        description = desc_override or "Redis Ping"
        try:
            return await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=description,
                func=self.redis.ping,
            )
        except Exception as _:
            raise KrakenProdcuerRedisConnectionException(f"[{description}] 도중 Redis ping 실패")

    async def close(self):
        """
        retry 로직을 붙힌 close 수행
        """
        try: 
            await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description="Redis 연결 종료",
                func=self.redis.close,
            )
        except Exception as e:
            raise KrakenProdcuerRedisCloseFailureException("Redis Client 종료 실패")

    async def fetch_all_data(self, redis_key: str):
        """
        특정 key의 모든 데이터를 가져오는 기능
        """
        try:
            return await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=f"[{redis_key}] KEY 데이터 GET ALL 요청",
                func=self.redis.smembers,
                func_args=(redis_key,)
            )
        except Exception as e:
            raise KrakenProdcuerRedisFetchDataException(f"{redis_key} 키 데이터 fetch 실패")

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        헬스 체크용 메소드
        """
        try:
            self.logger.info_start(description="헬스 체크")
            pong = await self._ping_with_retry(desc_override="헬스 체크 - Redis 연결 상태 확인")
            if pong:
                status = KrakenProducerComponentHealthStatus(component_name=self.config.component_name,
                                                    component=self, is_healthy=pong,
                                                    health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                                                    last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                                                    message=f"{self.config.component_name} 헬스체크 성공",
                                                    )
                self.logger.info_success(description="헬스 체크")
            else:
                status = KrakenProducerComponentHealthStatus(component_name=self.config.component_name,
                                                    component=self, is_healthy=False,
                                                    health_status_code=KrakenProducerStatusCodeEnum.CLIENT_FAIL_TO_CONNECT.value,
                                                    last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                                                    message=f"{self.config.component_name} 예외없이 헬스체크 실패",
                                                    )
                self.logger.warning_common(description="헬스 체크 중 예외 없는 Redis Ping 실패")
            return status
        except Exception as e:
            self.logger.exception_common(error=e, description="헬스 체크 중 Redis 연결")
            return KrakenProducerComponentHealthStatus(component_name=self.config.component_name,
                                                    component=self, is_healthy=False,
                                                    health_status_code=KrakenProducerStatusCodeEnum.ERROR.value,
                                                    last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                                                    message=f"{self.config.component_name} 헬스체크 중 오류: {str(e)}",
                                                    )
