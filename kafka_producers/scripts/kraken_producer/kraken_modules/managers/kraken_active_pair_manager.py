from typing import Set, Tuple, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.utils.data_models.kraken_active_pair_data_model import KrakenActivePairDataModel, KrakenSubscriptionKey
from kraken_modules.interfaces.kraken_base_health_tracked_component import KrakenBaseHealthTrackedComponent
from kraken_modules.interfaces.kraken_base_component_with_config import KrakenBaseComponentWithConfig
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus


class KrakenActivePairManager(KrakenBaseHealthTrackedComponent, KrakenBaseComponentWithConfig):
    """
    Redis에서 구독 대상 거래쌍 정보를 불러오고, 현재 상태와 비교하여 변화 추적하는 클래스
    """
    def __init__(self, redis_client: KrakenRedisClient, redis_key: Optional[str] = "kraken:active_pairs", retry_num: Optional[int] = 5, retry_delay: Optional[int] = 2,):
        self.redis_client = redis_client
        self.redis_key = redis_key
        self.retry_num = retry_num
        self.retry_delay = retry_delay

        self.component_name: str = "ACTIVE PAIR MANAGER"
        self.current_active_pairs: List[KrakenActivePairDataModel] = list()
        self.current_active_subscription_key: Set[KrakenSubscriptionKey] = set()
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.component_name,)

    async def initialize_active_pair_manager(self):
        """최초 상태 동기화"""
        self.logger.info_start(description="Kraken 거래쌍 매니저 초기화",)
        init_desc_msg = "Redis에서 초기 거래쌍 로딩"
        await self.redis_client.initialize_redis_client()
        await self.refresh(logging_msg=init_desc_msg)
        self.logger.info_success(description="Kraken 거래쌍 매니저 초기화",)

    async def refresh(self, description: str) -> Tuple[Set[str], Set[str]]:
        """
        Redis에서 최신 거래쌍을 불러오고,
        기존 거래쌍과 비교하여 (신규 구독, 구독 해제) 목록 반환

        :return: (새로운 구독할 키, 제거할 구독 키)
        """
        try:
            self.logger.info_start(description="활성 거래쌍 Refresh")
            redis_raw_data = await self._fetch_pairs_from_redis(description=description)

            redis_pairs = [KrakenActivePairDataModel(**redis_raw_pair) for redis_raw_pair in redis_raw_data]
            redis_subscription_keys = set([redis_pair.to_subscription_key() for redis_pair in redis_pairs])

            subscription_keys_to_add = redis_subscription_keys - self.current_active_subscription_key
            subscription_keys_to_delete = self.current_active_subscription_key - redis_subscription_keys

            if subscription_keys_to_add:
                self.logger.warning_common(description=f"새롭게 구독할 거래쌍 {len(subscription_keys_to_add)}개",)
            if subscription_keys_to_delete:
                self.logger.warning_common(description=f"구독 취소할 거래쌍 {len(subscription_keys_to_delete)}개",)

            # 상태 업데이트
            self.current_active_pairs = redis_pairs
            self.current_active_subscription_key = redis_subscription_keys
            self.logger.info_success(description="활성 거래쌍 Refresh")
            return subscription_keys_to_add, subscription_keys_to_delete
        except Exception as e:
            self.logger.exception_common(error=e, description="활성 거래쌍 Refresh")
            raise e

    async def _fetch_pairs_from_redis(self, description: str) -> Set[str]:
        """
        Redis에서 데이터를 가져오는 함수
        - 데이터를 가져오고 반환하는 역할만 수행
        """
        try:
            self.logger.info_start("Redis에서 거래쌍 정보 읽기")
            redis_raw_data = await custom_retry(
                logger=self.logger,
                retry_num=self.redis_client.retry_num,
                retry_delay=self.redis_client.retry_delay,
                conn_timeout=self.redis_client.conn_timeout,
                description=description,
                func=self.redis_client.fetch_all_data,
                func_kwargs=self.redis_key,
            )
            self.logger.info_success("Redis에서 거래쌍 정보 읽기")
            return redis_raw_data
        except Exception as e:
            self.logger.exception_common(error=e, description="Redis에서 거래쌍 정보 읽기")
            raise e

    def get_current_pairs(self) -> Optional[List[KrakenActivePairDataModel]]:
        """현재 메모리에 저장된 거래쌍 반환"""
        if self.current_active_pairs:
            self.logger.warning_common(f"{len(self.current_active_pairs)} 개 거래쌍 조회")
            return self.current_active_pairs.copy()
        else:
            self.logger.warning_common("저장된 거래쌍 없는 상황에서 거래쌍 조회")
            return None

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        self.logger.info_start(description="ActivePairManager 헬스 체크")
        if self.current_active_pairs:
            is_healthy = len(self.current) > 0
        else:
            is_healthy = False
        message = f"{len(self.current_active_pairs)}개의 거래쌍 데이터 저장 중" if is_healthy else "불러온 거래쌍 없음"
        status = KrakenProducerComponentHealthStatus(
            component_name=self.component_name,
            component=self,
            is_healthy=is_healthy,
            health_status_code=KrakenProducerStatusCodeEnum.STARTED.value if is_healthy else KrakenProducerStatusCodeEnum.NO_DATA.value,
            last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
            message=message,
        )
        self.logger.info_success(description="ActivePairManager 헬스 체크 완료")
        return status


    async def update_component_status(self) -> bool:
        """
        자신의 status를 업데이트하는 메소드
        - 필요 시 async 사용
        """
        new_status = await self.check_component_health()
        self.status_manager.update_manager_status(component_name=self.component_name, new_status=new_status)