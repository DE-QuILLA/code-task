from enum import Enum, unique


@unique
class KrakenExitCodeEnum(Enum):
    # 0번대: 성공
    SUCCESS = 0

    # 100 번대: Redis Client 관련 Custom Excpetion
    REDIS_CONNECTION_ERR = 101
    REDIS_CANNOT_CLOSE_ERR = 102

    # 200 번대: REST Client 관련 Custom Exception
    API_HTTP_ERR = 201

    # 300 번대: REST API Collector 관련 Custom Exception
    ERROR_IN_API_RESPONSE_ERR = 301
    NO_DATA_IN_API_RESPONSE_ERR = 302
    INVALID_KEY_VALUE_ERR = 303
    PRODUCER_API_CALL_FAIL_ERR = 304

    # 800번대: 개발자 잘못 (잘못된 ARG 등)
    INVALID_ARGS_ERR = 801
    JSON_LOAD_ERR = 802

    # 기타 구분되지 않은 에러
    UNKNOWN_ERR = 999  # 정의되지 않은 에러 발생 시 (위의 모든 에러를 지나 Exception 상속 클래스일 경우)
