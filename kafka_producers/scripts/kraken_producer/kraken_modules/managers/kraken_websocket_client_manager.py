from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.clients.kraken_websocket_client import KrakenWebSocketClient
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.interfaces.base_health_tracked_component import BaseHealthTrackedComponent

class KrakenWebSocketClientManager(BaseHealthTrackedComponent):
    def __init__(self, status_manager_config: KrakenProducerStatusManager, ):
        self.status_manager = status_manager