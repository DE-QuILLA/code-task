from enums.kraken_exit_code_enum import KrakenProducerExitCodeEnum
from kraken_modules.utils.exceptions import (
    # Kafka Client
    KrakenProducerKafkaClientCloseFailureException,
    KrakenProducerKafkaClientConnectionException,
    KrakenProducerNotValidMessageTypeException,
    KrakenProducerProduceFailureException,

    # Redis Client
    KrakenProdcuerRedisConnectionException,
    KrakenProdcuerRedisFetchDataException,
    KrakenProdcuerRedisCloseFailureException,

    # Web Socket Client
    KrakenProducerWebSocketClientConnectionException,
    KrakenProducerWebSocketClientMessageSendFailureException,
    KrakenProducerWebSocketClientSubscriptionFailureException, 
    KrakenProducerWebSocketClientUnsubscriptionFailureException,

    # Active Symbol Manager
    KrakenProducerActiveSymbolManagerRefreshException,

    # ALL CUSTOM EXCEPTIONS
    ALL_CUSTOM_EXCEPTIONS,

    # SUCCESS
    KrakenScriptSuccess,
)


# 순서에 주의할 것 => 위에서 부터 하나씩 검사할 수 밖에 없음.
EXCEPTION_TO_EXIT_CODE = {
    # 1. Kafka Client
    KrakenProducerKafkaClientCloseFailureException: KrakenProducerExitCodeEnum.KAFKA_CLIENT_CLOSE_FAIL_ERR,
    KrakenProducerKafkaClientConnectionException: KrakenProducerExitCodeEnum.KAFKA_CLIENT_CONNECTION_FAIL_ERR,
    KrakenProducerNotValidMessageTypeException: KrakenProducerExitCodeEnum.KAFKA_CLIENT_INVALID_MESSAGE_ERR,
    KrakenProducerProduceFailureException: KrakenProducerExitCodeEnum.KAFKA_CLIENT_PRODUCE_FAIL_ERR,

    # 2. Redis Client
    KrakenProdcuerRedisConnectionException: KrakenProducerExitCodeEnum.REDIS_CONNECTION_FAIL_ERR,
    KrakenProdcuerRedisFetchDataException: KrakenProducerExitCodeEnum.REDIS_FETCH_FAIL_ERR,
    KrakenProdcuerRedisCloseFailureException: KrakenProducerExitCodeEnum.REDIS_CLOSE_FAIL_ERR,

    # 3. Web Socket Client
    KrakenProducerWebSocketClientConnectionException: KrakenProducerExitCodeEnum.WS_CONNECTION_FAIL_ERR,
    KrakenProducerWebSocketClientMessageSendFailureException: KrakenProducerExitCodeEnum.WS_MESSAGE_SEND_FAIL_ERR,
    KrakenProducerWebSocketClientSubscriptionFailureException: KrakenProducerExitCodeEnum.WS_SUBSCRIBE_FAIL_ERR, 
    KrakenProducerWebSocketClientUnsubscriptionFailureException: KrakenProducerExitCodeEnum.WS_UNSUBSCRIBE_FAIL_ERR,

    # 4. 아직 정의되지 않은 에러의 경우
    Exception: KrakenProducerExitCodeEnum.UNKNOWN_EXCEPTION,

    # 5. 성공
    KrakenScriptSuccess: KrakenProducerExitCodeEnum.SUCCESS,
}

def get_exitcode_from_exception(e: Exception):
    for error, code in EXCEPTION_TO_EXIT_CODE:
        if isinstance(e, error):
            return code.value
