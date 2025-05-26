# custom
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.clients import KrakenRedisClient
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.managers import KrakenProducerStatusManager
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.config_models import KrakenActiveSymbolManagerConfigModel
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum
from kraken_modules.utils.wrapper import custom_retry
from kraken_modules.utils.exceptions import (
    KrakenProducerActiveSymbolManagerRefreshException,
)

# libraries
from typing import Set, Tuple, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo


class KrakenActiveSymbolManager(KrakenBaseComponent):
    """
    Redis에서 구독 대상 거래쌍 정보를 불러오고, 현재 상태와 비교하여 변화 추적하는 클래스
    """

    def __init__(
        self,
        config: KrakenActiveSymbolManagerConfigModel,
        redis_client: KrakenRedisClient,
        status_manager: KrakenProducerStatusManager,
    ):
        # config 객체
        self.config: KrakenActiveSymbolManagerConfigModel = config

        # 동적 초기화, 외부 객체 주입
        self.redis_client: KrakenRedisClient = redis_client
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.current_active_symbols: Set[str] = set()
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(
            logger_name=self.config.component_name,
        )

    async def initialize_active_pair_manager(self):
        """
        최초 상태 동기화
        """
        try:
            self.logger.info_start(
                description="Kraken 거래쌍 매니저 초기화",
            )
            await self.refresh()
            await self.status_manager.register_component(
                component_name=self.config.component_name, new_component=self
            )
            self.logger.info_success(
                description="Kraken 거래쌍 매니저 초기화",
            )
        except Exception as e:
            self.logger.exception_common(
                error=e,
                description="Kraken 거래쌍 매니저 초기화",
            )
            # 내부 에러 그대로 raise
            raise

    async def refresh(
        self,
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Redis에서 거래소 별 symbol들을 불러와서
        기존 거래쌍과 비교하여 (신규 구독, 구독 해제) 목록 반환

        :return: (새로운 구독할 심볼, 제거할 구독 심볼)
        """
        try:
            self.logger.info_start(description="활성 심볼 Refresh")
            new_symbols = set(
                await self._fetch_symbols_from_redis(
                    redis_key=self.config.common_redis_key
                )
            )

            old_kraken_symbols = self.current_active_symbols

            new_subscription_symbols = new_symbols - old_kraken_symbols
            new_unsubscription_symbols = old_kraken_symbols - new_symbols

            if new_subscription_symbols:
                self.logger.warning_common(
                    description=f"새롭게 구독할 심볼 {len(new_subscription_symbols)}개",
                )
            if new_unsubscription_symbols:
                self.logger.warning_common(
                    description=f"구독 취소할 심볼 {len(new_unsubscription_symbols)}개",
                )

            # 상태 업데이트
            self.current_active_symbols = new_symbols
            self.logger.info_success(
                description=f"{len(self.current_active_symbols)}개 활성 심볼 Refresh"
            )

            # KRW, USD 통화 붙혀서 리스트로 바꾸고 리턴하기
            return (
                self._add_currency(new_symbols),
                self._add_currency(new_subscription_symbols),
                self._add_currency(new_unsubscription_symbols),
            )
        except Exception as e:
            self.logger.exception_common(error=e, description="활성 심볼 Refresh")
            raise KrakenProducerActiveSymbolManagerRefreshException(
                "활성 심볼 Refresh 중 실패"
            )

    @staticmethod
    def _add_currency(symbols: Set[str]) -> List[str]:
        """
        수집하는 기준 통화를 심볼에 붙혀주는 헬퍼
        """
        currencies = ["KRW", "USD"]
        return [
            symbol + f"/{currency}" for symbol in symbols for currency in currencies
        ]

    async def _fetch_symbols_from_redis(
        self,
        redis_key: str,
    ) -> Set[str]:
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
                func_args=(redis_key,),
            )
            self.logger.info_success(f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기")
            return redis_raw_data
        except Exception as e:
            self.logger.exception_common(
                error=e, description=f"Redis에서 {redis_key} 키의 거래쌍 정보 읽기"
            )
            # Redis Client 단의 에러를 그대로 raise
            raise

    def get_current_pairs(self) -> List[str]:
        """현재 메모리에 저장된 거래쌍 반환"""
        if self.current_active_symbols:
            self.logger.warning_common(
                f"{len(self.current_active_symbols)} 개 거래쌍 조회"
            )
            return self._add_currency(self.current_active_symbols)
        else:
            self.logger.warning_common("저장된 거래쌍 없는 상황에서 거래쌍 조회")
            return None

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        Pair Manager의 헬스체크 함수
        """
        self.logger.info_start(description="ActivePairManager 헬스 체크")
        if self.current_active_symbols:
            is_healthy = len(self.current_active_symbols) > 0
        else:
            is_healthy = False
        message = (
            f"{len(self.current_active_symbols)}개의 거래쌍 데이터 저장 중"
            if is_healthy
            else "불러온 거래쌍 없음"
        )
        status = KrakenProducerComponentHealthStatus(
            component_name=self.config.component_name,
            component=self,
            is_healthy=is_healthy,
            health_status_code=KrakenProducerStatusCodeEnum.STARTED.value
            if is_healthy
            else KrakenProducerStatusCodeEnum.NO_DATA.value,
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
        self.status_manager.update_manager_status(
            component_name=self.config.component_name, new_status=new_status
        )
