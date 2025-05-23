from enum import Enum, unique


@unique
class KrakenProducerExitCodeEnum(Enum):
    # 0번대: 성공
    SUCCESS = 0

    # 100 번대: Kafka Client 에러
    KAFKA_CLIENT_CONNECTION_FAIL_ERR = 101
    KAFKA_CLIENT_CLOSE_FAIL_ERR = 102
    KAFKA_CLIENT_INVALID_MESSAGE_ERR = 103
    KAFKA_CLIENT_PRODUCE_FAIL_ERR = 104

    # 200 번대: Redis Client 에러
    REDIS_CONNECTION_FAIL_ERR = 101
    REDIS_FETCH_FAIL_ERR = 102
    REDIS_CLOSE_FAIL_ERR = 103

    # 300 번대: Web Socket Client
    WS_CONNECTION_FAIL_ERR = 301
    WS_MESSAGE_SEND_FAIL_ERR = 302
    WS_SUBSCRIBE_FAIL_ERR = 303
    WS_UNSUBSCRIBE_FAIL_ERR = 304

    # 400 번대: Active Symbol Manager
    ACTIVE_SYMBOL_REFRESH_FAIL_ERR = 401

    # 기타 구분되지 않은 에러
    UNKNOWN_EXCEPTION = 999  # 정의되지 않은 에러 발생 시 (위의 모든 에러를 지나 Exception 상속 클래스일 경우)
