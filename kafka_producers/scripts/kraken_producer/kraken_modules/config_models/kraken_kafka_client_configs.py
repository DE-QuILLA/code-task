from pydantic import BaseModel
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel
from typing import Dict, Optional

class KrakenKafkaClientConfigModel(KrakenBaseConfigModel):
    bootstrap_server: str
    health_topic_name: str
    component_name: str = "KAFKA CLIENT"
    acks: Optional[str] = "1"
    retry_num: Optional[int] = 5
    retry_delay: Optional[int] = 2
    conn_timeout: Optional[int] = 20
    acks: Optional[str] = "1"
