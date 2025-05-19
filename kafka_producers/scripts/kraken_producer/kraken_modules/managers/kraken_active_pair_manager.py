import json
from typing import Set, Tuple, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.utils.data_models.kraken_active_pair_data_model import KrakenActivePairDataModel, KrakenSubscriptionKey
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus
from kraken_modules.config_models import KrakenActivePairManagerConfigModel


class KrakenActivePairManager(KrakenBaseComponent):
    """
    Redis에서 구독 대상 거래쌍 정보를 불러오고, 현재 상태와 비교하여 변화 추적하는 클래스
    """
    def __init__(self, config: KrakenActivePairManagerConfigModel, redis_client: KrakenRedisClient, status_manager: KrakenProducerStatusManager):
        # config 객체
        self.config: KrakenActivePairManagerConfigModel = config

        # 동적 초기화, 외부 객체 주입
        self.redis_client: KrakenRedisClient = redis_client
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.current_active_symbols: Set[str] = set()
        # self.current_active_subscription_key: Set[KrakenSubscriptionKey] = set()
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.config.component_name,)

    async def initialize_active_pair_manager(self):
        """최초 상태 동기화"""
        self.logger.info_start(description="Kraken 거래쌍 매니저 초기화",)
        init_desc_msg = "Redis에서 초기 거래쌍 로딩"
        await self.refresh(logging_msg=init_desc_msg)
        await self.status_manager.register_component(component_name=self.config.component_name, new_component=self)
        self.logger.info_success(description="Kraken 거래쌍 매니저 초기화",)

    async def refresh(self, description: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Redis에서 거래소 별 symbol들을 불러와서
        기존 거래쌍과 비교하여 (신규 구독, 구독 해제) 목록 반환

        :return: (새로운 구독할 심볼, 제거할 구독 심볼)
        """
        try:
            self.logger.info_start(description="활성 심볼 Refresh")
            fetched_kraken_symbols = set(await self._fetch_pairs_from_redis(redis_key=self.config.kraken_redis_key))
            fetched_upbit_symbols = set(await self._fetch_pairs_from_redis(redis_key=self.config.upbit_redis_key))
            fetched_binance_symbols = set(await self._fetch_pairs_from_redis(redis_key=self.config.binance_redis_key))

            new_kraken_symbols = fetched_kraken_symbols & fetched_upbit_symbols & fetched_binance_symbols
            old_kraken_symbols = self.current_active_symbols

            new_subscription_symbols = new_kraken_symbols - old_kraken_symbols
            new_unsubscription_symbols = old_kraken_symbols - new_kraken_symbols

            if new_subscription_symbols:
                self.logger.warning_common(description=f"새롭게 구독할 심볼 {len(new_subscription_symbols)}개",)
            if new_unsubscription_symbols:
                self.logger.warning_common(description=f"구독 취소할 심볼 {len(new_unsubscription_symbols)}개",)

            # 상태 업데이트
            self.current_active_symbols = new_kraken_symbols
            self.logger.info_success(description="활성 심볼 Refresh")

            # KRW, USD 통화 붙혀서 리스트로 바꾸고 리턴하기
            return self._add_currency(new_kraken_symbols), self._add_currency(new_subscription_symbols), self._add_currency(new_unsubscription_symbols)
        except Exception as e:
            self.logger.exception_common(error=e, description="활성 심볼 Refresh")
            raise e

    @staticmethod
    def _add_currency(symbols: Set[str]):
        return [func(symbol) for symbol in symbols for func in (lambda x: x + '/KRW', lambda y: y + '/USD')]


    async def _fetch_pairs_from_redis(self, redis_key: str,) -> Set[str]:
        """
        Redis에서 특정 key의 데이터를 가져오는 함수
        - 데이터를 가져오고 반환하는 역할만 수행
        """
        try:
            self.logger.info_start(f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기")
            description = f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기"
            redis_raw_data = await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=description,
                func=self.redis_client.fetch_all_data,
                func_args=redis_key,
            )
            self.logger.info_success(f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기")
            return redis_raw_data
        except Exception as e:
            self.logger.exception_common(error=e, description=f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기")
            raise e

    def get_current_pairs(self) -> Optional[List[KrakenActivePairDataModel]]:
        """현재 메모리에 저장된 거래쌍 반환"""
        if self.current_active_symbols:
            self.logger.warning_common(f"{len(self.current_active_symbols)} 개 거래쌍 조회")
            return self.current_active_symbols.copy()
        else:
            self.logger.warning_common("저장된 거래쌍 없는 상황에서 거래쌍 조회")
            return None

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        self.logger.info_start(description="ActivePairManager 헬스 체크")
        if self.current_active_symbols:
            is_healthy = len(self.current_active_symbols) > 0
        else:
            is_healthy = False
        message = f"{len(self.current_active_symbols)}개의 거래쌍 데이터 저장 중" if is_healthy else "불러온 거래쌍 없음"
        status = KrakenProducerComponentHealthStatus(
            component_name=self.config.component_name,
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
        self.status_manager.update_manager_status(component_name=self.config.component_name, new_status=new_status)