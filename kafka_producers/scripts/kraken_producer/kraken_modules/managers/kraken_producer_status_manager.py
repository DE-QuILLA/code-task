from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Type, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from kraken_modules.utils.exceptions.kraken_custom_exceptions import KrakenProducerNotValidStatusCodeException
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger, get_start_info_msg, get_success_info_msg, get_warning_msg
import json

class KrakenProducerComponentHealthStatus(BaseModel):
    component_name: str           # 컴포넌트 명
    type_of_component: Type[Any]  # 저장되는 객체 타입
    is_healthy: bool = False
    health_status_code: int = KrakenProducerStatusCodeEnum.NOT_STARTED  # 정의된 스테이터스 코드
    last_checked_at: datetime        # 마지막 체크된 시각
    message: Optional[str] = None    # 메시지 저장 (Optional)

    @field_validator("health_status_code", mode="before")
    @classmethod
    def health_code_validator(cls, health_status_code_input):
        if isinstance(health_status_code_input, int) and health_status_code_input in {e.value for e in KrakenProducerStatusCodeEnum}:
            return health_status_code_input
        else:
            # TODO: 명시적인 raise가 적절할지 판단해보기
            # raise KrakenProducerNotValidStatusCodeException
            return KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_CODE


class KrakenProducerStatusManager:
    def __init__(self):
        self._status_map: Dict[str, KrakenProducerComponentHealthStatus] = {}
        self.logger = get_stdout_logger(logger_name="STATUS MANAGER")

    def register_component(self, component_name: str, type_of_component: Type[Any], is_healthy: bool = False, health_status_code: int = KrakenProducerStatusCodeEnum.NOT_STARTED, last_checked_at: datetime = datetime.now(ZoneInfo("Asia/Seoul")), message: Optional[str] = None):
        self.logger.info(get_start_info_msg(description=f"{component_name} 스테이터스 관리 대상 등록"))
        self._status_map[component_name] = KrakenProducerComponentHealthStatus(
            component_name=component_name,
            type_of_component=type_of_component,
            is_healthy=is_healthy,
            health_status_code=health_status_code,
            last_checked_at=last_checked_at,
            message=message if message else f"{component_name} Status Manager에 첫 등록!",
        )
        self.logger.info(get_success_info_msg(description=f"{component_name} 스테이터스 관리 대상 등록"))

    def update_status(self, component_name: str, is_healthy: bool, health_status_code: int, message: Optional[str] = None):
        self.logger.info(get_start_info_msg(description=f"{component_name} 스테이터스 업데이트"))

        if component_name not in self._status_map:
            self.logger.warning(get_warning_msg(description=f"{component_name} 상태 관리 대상 확인 불가"))
            return

        self._status_map[component_name].is_healthy = is_healthy
        
        if isinstance(health_status_code, int) and health_status_code in {e.value for e in KrakenProducerStatusCodeEnum}:
            self._status_map[component_name].health_status_code = health_status_code
        else:
            self.is_healthy = False
            self._status_map[component_name].health_status_code = KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_CODE
            self.logger.warning(get_warning_msg(description=f"{component_name} 스테이터스 업데이트 중 잘못된 스테이터스 코드 입력"))
        
        self._status_map[component_name].last_checked_at = datetime.now(ZoneInfo("Asia/Seoul"))

        if message:
            self._status_map[component_name].message = message
        else:
            self._status_map[component_name].message = f"{component_name} 상태 업데이트됨, healthy: {self._status_map[component_name].is_healthy}"
        
        self.logger.info(get_success_info_msg(description=f"{component_name} 스테이터스 업데이트"))

    def get_status(self, component_name: str) -> Optional[KrakenProducerComponentHealthStatus]:
        return self._status_map.get(component_name, None)  # 없는 component에 대한 응답 None으로 고정

    def get_all(self) -> Dict[str, KrakenProducerComponentHealthStatus]:
        return self._status_map
    
    def get_all_by_api(self) -> Dict:
        return {
        k: v.model_dump() for k, v in self._status_map.items()
    }
