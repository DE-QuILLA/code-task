# init

"""
Kafka, Redis 등과 연결하는 Client를 작성하는 모듈
- KrakenKafkaClient: 카프카와 연결
- KrakenRedisClient: 레디스와 연결
- KrakenWebSocketClient: 크라켄 웹소켓과 연결
"""

from .kraken_kafka_client import KrakenKafkaClient
from .kraken_redis_client import KrakenRedisClient
from .kraken_websocket_client import KrakenWebSocketClient
