class KrakenBaseETLException(Exception):
    """
    Kraken에서 데이터를 가져오고 처리하는 과정에서 직접 정의하는 에러의 부모 클래스
    - 기본적인 동작은 에러 메시지 전달 외에 없음.
    - 코드 내 명세화를 위한 작성
    """

    def __init__(self, message):
        super().__init__(message)


# 1. Redis Client
class KrakenRedisClientConnectionException(KrakenBaseETLException):
    """Redis와 연결 실패 Exception"""

    pass


class KrakenRedisClientCanNotCloseException(KrakenBaseETLException):
    """Redis 연결 종료 실패"""

    pass


# 2. Rest Client


class KrakenRESTClientHTTPException(KrakenBaseETLException):
    """HTTP 예외(aiohttp.ClientResponseError) 관련 예외"""

    pass


# 3. REST API COLLECTOR


class KrakenErrorInAPIResponseException(KrakenBaseETLException):
    """Kraken Rest api의 Error 필드에 값 존재"""

    pass


class KrakenAPIResponseNoDataException(KrakenBaseETLException):
    """Kraken Rest API의 응답 데이터 비어있음"""

    pass


class KrakenAPIResponseValueException(KrakenBaseETLException):
    """API 응답의 필드 구조가 예상과 다를 때"""

    pass


class KrakenProducerAPICallFailException(KrakenBaseETLException):
    """API 응답의 필드 구조가 예상과 다를 때"""

    pass


ALL_CUSTOM_EXCEPTIONS = [
    KrakenRedisClientConnectionException,
    KrakenRedisClientCanNotCloseException,
]
