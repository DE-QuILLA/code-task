# custom
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum

# libraries
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import field_validator, BaseModel
from typing import Optional


class KrakenProducerComponentHealthStatus(BaseModel):
    component_name: str  # 컴포넌트 명
    component: KrakenBaseComponent  # 관리되는 컴포넌트 자체
    is_healthy: bool = False
    health_status_code: int = (
        KrakenProducerStatusCodeEnum.NOT_STARTED.value
    )  # 정의된 스테이터스 코드
    last_checked_at: datetime = datetime.now(
        ZoneInfo("Asia/Seoul")
    )  # 마지막 체크된 시각
    message: Optional[str] = None  # 메시지 저장 (Optional)

    @field_validator("health_status_code", mode="before")
    @classmethod
    def health_code_validator(cls, health_status_code_input):
        if isinstance(health_status_code_input, int) and health_status_code_input in {
            e.value for e in KrakenProducerStatusCodeEnum
        }:
            return health_status_code_input
        else:
            return KrakenProducerStatusCodeEnum.NOT_VALID_STATUS_INPUT.value
