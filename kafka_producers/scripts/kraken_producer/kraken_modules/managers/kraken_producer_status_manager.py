from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Type, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.interfaces.kraken_base_component_with_config import KrakenBaseComponentWithConfig
from kraken_modules.interfaces.kraken_base_health_tracked_component import KrakenBaseHealthTrackedComponent
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger


class KrakenProducerComponentHealthStatus(BaseModel):
    component_name: str                          # 컴포넌트 명
    component: KrakenBaseHealthTrackedComponent  # 관리되는 컴포넌트 자체
    is_healthy: bool = False
    health_status_code: int = KrakenProducerStatusCodeEnum.NOT_STARTED.value  # 정의된 스테이터스 코드
    last_checked_at: datetime = datetime.now(ZoneInfo("Asia/Seoul"))         # 마지막 체크된 시각
    message: Optional[str] = None     # 메시지 저장 (Optional)

    @field_validator("health_status_code", mode="before")
    @classmethod
    def health_code_validator(cls, health_status_code_input):
        if isinstance(health_status_code_input, int) and health_status_code_input in {e.value for e in KrakenProducerStatusCodeEnum}:
            return health_status_code_input
        else:
            return KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_INPUT.value


class KrakenProducerStatusManager(KrakenBaseComponentWithConfig):
    def __init__(self):
        self.component_name: str = "STATUS MANAGER"
        self._status_map: Dict[str, KrakenProducerComponentHealthStatus] = {}
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name=self.component_name)

    async def register_component(self, component_name: str, new_component: KrakenBaseHealthTrackedComponent):
        """새로운 상태 관리 컴포넌트 등록"""
        self.logger.info_start(description=f"{component_name} 스테이터스 관리 대상 등록")
        self._status_map[component_name] = await new_component.check_component_health()
        self.logger.info_success(description=f"{component_name} 스테이터스 관리 대상 등록")

    def update_manager_status(self, component_name: str, new_status: KrakenProducerComponentHealthStatus) -> bool:
        """스테이터스 매니저가 관리하는 스테이터스를 동적 갱신"""
        self.logger.info_start(description=f"{component_name} 스테이터스 업데이트")

        if component_name not in self._status_map:
            self.logger.warning_common(description=f"{component_name} 상태 관리 대상 확인 불가")
            self.logger.warning_common(description=f"{component_name} health_status_code: NOT_VALID_STATUS_CODE 로 변경")
            new_status.health_status_code = KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_INPUT.value

        self._status_map[component_name] = new_status
        self.logger.info_success(description=f"{component_name} 스테이터스 업데이트")

    def get_one_component_status(self, component_name: str) -> Optional[KrakenProducerComponentHealthStatus]:
        return self._status_map.get(component_name, None)  # 없는 component에 대한 응답 None으로 고정

    def get_all_component_status(self) -> Dict[str, KrakenProducerComponentHealthStatus]:
        return self._status_map

    def get_all_by_api(self) -> Dict:
        return {
        k: v.model_dump() for k, v in self._status_map.items()
    }

    async def refresh_all_component_statuses(self):
        for name, status_obj in self._status_map.items():
            await status_obj.component.update_component_status()
