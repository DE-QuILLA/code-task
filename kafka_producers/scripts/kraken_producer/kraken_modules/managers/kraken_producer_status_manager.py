# custom
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.utils.enums.kraken_producer_status_code_enum import (
    KrakenProducerStatusCodeEnum,
)
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger

# libraries
from typing import Optional, Dict


class KrakenProducerStatusManager:
    """
    KrakenStandardLogger 클래스와 함께 상태를 관리하지 않고 Config 객체를 활용하지 않는 객체
    """

    def __init__(self):
        self.component_name: str = "STATUS MANAGER"
        self._status_map: Dict[str, KrakenProducerComponentHealthStatus] = {}
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(
            logger_name=self.component_name
        )

    async def register_component(
        self, component_name: str, new_component: KrakenBaseComponent
    ):
        """새로운 상태 관리 컴포넌트 등록"""
        try:
            self.logger.info_start(
                description=f"{component_name} 스테이터스 관리 대상 등록"
            )
            self._status_map[
                component_name
            ] = await new_component.check_component_health()
            self.logger.info_success(
                description=f"{component_name} 스테이터스 관리 대상 등록"
            )
        except Exception as e:
            self.logger.exception_common(
                error=e, description=f"{component_name} 스테이터스 관리 대상 등록"
            )
            # 컴포넌트별 내부 로직에서 에러 그대로 raise
            raise

    def update_manager_status(
        self, component_name: str, new_status: KrakenProducerComponentHealthStatus
    ) -> bool:
        """스테이터스 매니저가 관리하는 스테이터스를 동적 갱신"""
        self.logger.info_start(description=f"{component_name} 스테이터스 업데이트")

        if component_name not in self._status_map:
            self.logger.warning_common(
                description=f"{component_name} 상태 관리 대상 확인 불가"
            )
            self.logger.warning_common(
                description=f"{component_name} health_status_code: NOT_VALID_STATUS_CODE 로 변경"
            )
            new_status.health_status_code = (
                KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_INPUT.value
            )

        self._status_map[component_name] = new_status
        self.logger.info_success(description=f"{component_name} 스테이터스 업데이트")

    def get_one_component_status(
        self, component_name: str
    ) -> Optional[KrakenProducerComponentHealthStatus]:
        """
        한개 컴포넌트의 상태 정보 얻는 함수
        """
        return self._status_map.get(
            component_name, None
        )  # 없는 component에 대한 응답 None으로 고정

    def get_all_component_status(
        self,
    ) -> Dict[str, KrakenProducerComponentHealthStatus]:
        """
        전체 컴포넌트의 상태 정보 얻는 함수
        """
        return self._status_map

    def get_all_by_api(self) -> Dict:
        """
        api 응답 형식에 맞춘 모든 함수 정보를 얻는 함수
        """
        return {k: v.model_dump() for k, v in self._status_map.items()}

    async def refresh_one_component_statuses(self, status_managed_component_name: str):
        """
        한 상태 관리 컴포넌트의 상태 정보 갱신
        """
        await self._status_map[
            status_managed_component_name
        ].component.update_component_status()

    async def refresh_all_component_statuses(self):
        """
        모든 상태 관리 컴포넌트의 상태 정보 갱신
        """
        try:
            for name, status_obj in self._status_map.items():
                self.logger.info_start(f"{name} 컴포넌트 헬스 체크 상태 갱신")
                await status_obj.component.update_component_status()
                self.logger.info_success(f"{name} 컴포넌트 헬스 체크 상태 갱신")
        except Exception as e:
            self.logger.exception_common(
                error=e, description=f"{name} 컴포넌트 헬스 체크 상태 갱신"
            )
            # 그대로 raise
            raise
