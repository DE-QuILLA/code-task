from kraken_modules.utils.exceptions import *
from enums.kraken_exit_code_enum import KrakenProducerExitCodeEnum
from exceptions.kraken_success import KrakenScriptSuccess
import redis.asyncio as aioredis

# 순서에 주의할 것 => 위에서 부터 하나씩 검사할 수 밖에 없음.
EXCEPTION_TO_EXIT_CODE = {
    # 0. 커스텀 에러 객체
    KrakenProducerKafkaClientException: KrakenProducerExitCodeEnum.KRAKEN_KAFKA_CLIENT_EXCEPTION,

    # # 1. asyncio 에러
    # asyncio.TimeoutError: KrakenExitCodeEnum.KRAKEN_API_TIMEOUT_ERR,
    # aiohttp.ClientError: KrakenExitCodeEnum.KRAKEN_API_HTTP_ERR,

    # # 2. redis 관련 에러
    aioredis.ConnectionError: KrakenProducerBaseException.REDIS_CONNECTION_EXCEPTION,
    # aioredis.RedisError: KrakenExitCodeEnum.REDIS_ERR,

    # # 3. 개발자 실수
    # NotImplementedError: KrakenExitCodeEnum.NOT_IMPLEMENTED_ERR,
    # TypeError: KrakenExitCodeEnum.INVALID_TYPE_ERR,

    # 4. 아직 정의되지 않은 에러의 경우
    Exception: KrakenProducerExitCodeEnum.UNKNOWN_EXCEPTION,

    # 5. 성공
    KrakenScriptSuccess: KrakenProducerExitCodeEnum.SUCCESS,
}

def get_exitcode_from_exception(e: Exception):
    for error, code in EXCEPTION_TO_EXIT_CODE:
        if isinstance(e, error):
            return code.value
