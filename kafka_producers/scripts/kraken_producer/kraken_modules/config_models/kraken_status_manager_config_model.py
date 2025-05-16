from pydantic import BaseModel
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus
from kraken_modules.config_models.kraken_standarad_logger_config_model import KrakenStandardLoggerConfigModel
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from typing import Optional, Dict, Any

class KrakenStatusManagerConfigModel(BaseModel):
    _status_map: Optional[Dict[str, KrakenProducerComponentHealthStatus]]
    logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name="STATUS MANAGER")
