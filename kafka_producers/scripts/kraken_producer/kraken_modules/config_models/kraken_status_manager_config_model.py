# custom
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.logging import KrakenStdandardLogger

# libraries
from typing import Optional, Dict
from pydantic import BaseModel


class KrakenStatusManagerConfigModel(BaseModel):
    """Status Manager 컴포넌트 초기화용 config 모델"""

    _status_map: Optional[Dict[str, KrakenProducerComponentHealthStatus]]
    logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name="STATUS MANAGER")
