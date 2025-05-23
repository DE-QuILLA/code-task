# init

"""
종료 코드 및 에러 기반 로직 분기를 위한 커스텀 Exception 객체를 작성하는 모듈
-
"""

# Kafka Client
from .kraken_custom_exceptions import KrakenProducerKafkaClientCloseFailureException
from .kraken_custom_exceptions import KrakenProducerKafkaClientConnectionException
from .kraken_custom_exceptions import KrakenProducerNotValidMessageTypeException
from .kraken_custom_exceptions import KrakenProducerProduceFailureException

# Redis Client
from .kraken_custom_exceptions import KrakenProdcuerRedisConnectionException
from .kraken_custom_exceptions import KrakenProdcuerRedisFetchDataException
from .kraken_custom_exceptions import KrakenProdcuerRedisCloseFailureException

# Web Socket Client
from .kraken_custom_exceptions import KrakenProducerWebSocketClientConnectionException
from .kraken_custom_exceptions import (
    KrakenProducerWebSocketClientMessageSendFailureException,
)
from .kraken_custom_exceptions import (
    KrakenProducerWebSocketClientSubscriptionFailureException,
    KrakenProducerWebSocketClientUnsubscriptionFailureException,
)

# Active Pair Manager
from .kraken_custom_exceptions import KrakenProducerActiveSymbolManagerRefreshException

# ALL CUSTOM EXCEPTIONS
from .kraken_custom_exceptions import ALL_CUSTOM_EXCEPTIONS

# SUCCESS
from .kraken_success import KrakenScriptSuccess
