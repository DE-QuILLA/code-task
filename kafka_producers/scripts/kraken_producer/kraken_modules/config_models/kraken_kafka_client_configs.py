from kraken_modules.config_models import KrakenBaseConfigModel
from typing import Optional

class KrakenKafkaClientConfigModel(KrakenBaseConfigModel):
    bootstrap_server: str
    health_topic_name: str = "__kafka_health_check"
    component_name: str = "KAFKA CLIENT"
    acks: Optional[str] = "1"
