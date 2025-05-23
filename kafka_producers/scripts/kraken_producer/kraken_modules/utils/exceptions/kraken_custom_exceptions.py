from abc import ABC


class KrakenProducerBaseException(Exception):
    """
    Kraken에서 데이터를 가져오고 처리하는 Producer에서 직접 정의하는 에러의 부모 클래스
    - 기본적인 동작은 에러 메시지 전달 외에 없음.
    - 코드 내 명세화를 위한 작성
    """

    def __init__(self, message):
        super().__init__(message)


# Kafka Client Exceptions
class KrakenProducerKafkaClientConnectionException(KrakenProducerBaseException):
    """Kafka 연결 실패 시"""

    pass


class KrakenProducerKafkaClientCloseFailureException(KrakenProducerBaseException):
    """Kafka 클라이언트 종료 실패 시"""

    pass


class KrakenProducerNotValidMessageTypeException(KrakenProducerBaseException):
    """str이 아닌 메시지 발생 시"""

    pass


class KrakenProducerProduceFailureException(KrakenProducerBaseException):
    """메시지 produce 실패 시"""

    pass


# Redis Client Exceptions


class KrakenProdcuerRedisConnectionException(KrakenProducerBaseException):
    """Redis 연결 실패 시 발생 에러"""

    pass


class KrakenProdcuerRedisFetchDataException(KrakenProducerBaseException):
    """Redis 연결 실패 시 발생 에러"""

    pass


class KrakenProdcuerRedisCloseFailureException(KrakenProducerBaseException):
    """Redis 연결 실패 시 발생 에러"""

    pass


# Web Socket Client Exceptions


class KrakenProducerWebSocketClientConnectionException(KrakenProducerBaseException):
    pass


class KrakenProducerWebSocketClientMessageSendFailureException(
    KrakenProducerBaseException
):
    pass


class KrakenProducerWebSocketClientSubscriptionFailureException(
    KrakenProducerBaseException
):
    pass


class KrakenProducerWebSocketClientUnsubscriptionFailureException(
    KrakenProducerBaseException
):
    pass


# Active Pair Manager Exceptions


class KrakenProducerActiveSymbolManagerRefreshException(KrakenProducerBaseException):
    pass


ALL_CUSTOM_EXCEPTIONS = [
    KrakenProducerKafkaClientConnectionException,
    KrakenProducerKafkaClientCloseFailureException,
    KrakenProducerNotValidMessageTypeException,
    KrakenProducerProduceFailureException,
    KrakenProdcuerRedisConnectionException,
    KrakenProdcuerRedisFetchDataException,
    KrakenProdcuerRedisCloseFailureException,
    KrakenProducerWebSocketClientConnectionException,
    KrakenProducerWebSocketClientMessageSendFailureException,
    KrakenProducerWebSocketClientSubscriptionFailureException,
    KrakenProducerWebSocketClientUnsubscriptionFailureException,
    KrakenProducerActiveSymbolManagerRefreshException,
]
