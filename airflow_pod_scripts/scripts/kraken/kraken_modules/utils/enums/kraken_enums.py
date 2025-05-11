from enum import Enum, unique

@unique
class KrakenExitCodeEnum(Enum):
    # 0번대: 성공
    SUCCESS = 0

    # 100번대: 사용자 값 관련 에러
    INVALID_ARGS_ERR = 101
    INVALID_TYPE_ERR = 102
    JSON_LOAD_ERR = 103
    JSON_DUMPS_ERR = 104
    NOT_IMPLEMENTED_ERR = 199

    # 200번대: 외부 연결 도중 에러
    KRAKEN_API_ERROR_IN_RESPONSE_ERR = 201
    KRAKEN_API_NO_DATA_IN_RESPONSE_ERR = 202
    KRAKEN_API_HTTP_ERR = 203        # HTTP 요청 실패 관련 에러
    KRAKEN_API_TIMEOUT_ERR = 204     # aiohttp 요청 timeout 에러

    # 300번대: Redis 관련 에러
    REDIS_ERR = 300  # 레디스 관련 가장 상위 에러
    REDIS_CONNECTION_ERR = 301  # 레디스 연결 실패 에러

    # 기타 구분되지 않은 에러
    UNKNOWN_ERR = 999

