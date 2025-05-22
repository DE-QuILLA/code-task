from exceptions import (
    # 1. Redis 관련 에러
    KrakenRedisClientConnectionException,
    KrakenRedisClientCanNotCloseException,

    # 2. REST Client 관련 에러
    KrakenRESTClientHTTPException,

    # 3. Collector 관련 에러
    KrakenErrorInAPIResponseException,
    KrakenAPIResponseNoDataException,
    KrakenAPIResponseValueException,
    KrakenProducerAPICallFailException,

    # 4. 성공
    KrakenScriptSuccess
)
from enums import KrakenExitCodeEnum


EXCEPTION_TO_EXIT_ENUM = {
    # 1. Redis Client 쪽 실패
    KrakenRedisClientConnectionException: KrakenExitCodeEnum.REDIS_CONNECTION_ERR,
    KrakenRedisClientCanNotCloseException: KrakenExitCodeEnum.REDIS_CANNOT_CLOSE_ERR,

    # 2. REST Client 쪽 실패
    KrakenRESTClientHTTPException: KrakenExitCodeEnum.API_HTTP_ERR,

    # 3. API Collector 쪽 실패
    KrakenErrorInAPIResponseException: KrakenExitCodeEnum.ERROR_IN_API_RESPONSE_ERR,
    KrakenAPIResponseNoDataException: KrakenExitCodeEnum.NO_DATA_IN_API_RESPONSE_ERR,
    KrakenAPIResponseValueException: KrakenExitCodeEnum.INVALID_KEY_VALUE_ERR,
    KrakenProducerAPICallFailException: KrakenExitCodeEnum.PRODUCER_API_CALL_FAIL_ERR,

    # 4. 아직 정의되지 않은 에러의 경우
    Exception: KrakenExitCodeEnum.UNKNOWN_ERR,

    # 5. 성공
    KrakenScriptSuccess: KrakenExitCodeEnum.SUCCESS,
}

def get_exitcode_from_exception(e: Exception) -> int:
    for error, code in EXCEPTION_TO_EXIT_ENUM.items():
        if isinstance(e, error):
            return code.value
