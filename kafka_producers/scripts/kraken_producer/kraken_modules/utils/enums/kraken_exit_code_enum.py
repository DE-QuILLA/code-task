from enum import Enum, unique

@unique
class KrakenProducerExitCodeEnum(Enum):
    # 0번대: 성공
    SUCCESS = 0

    # 100번대: 사용자 값 관련 에러
    # INVALID_ARGS_ERR = 101     # argument 관련 문제 발생 시
    # INVALID_TYPE_ERR = 102     # Type Error 발생 시
    # JSON_LOAD_ERR = 103        # Json Load 실패 발생 시  
    # JSON_DUMPS_ERR = 104       # Json dumps 실패 발생 시
    # NOT_IMPLEMENTED_ERR = 199  # NotImplentedError 발생 시

    # 200번대: 외부 연결 도중 에러
    KRAKEN_KAFKA_CLIENT_EXCEPTION = 201        # Kafka 연결 실패 발생 시
    # KRAKEN_API_NO_DATA_IN_RESPONSE_ERR = 202  # 크라켄 API 응답의 데이터가 없을 때 발생
    # KRAKEN_API_HTTP_ERR = 203                 # HTTP 요청 실패 관련 상속 관계 최상위 ClientError 에러 발생 시
    # KRAKEN_API_TIMEOUT_ERR = 204              # aiohttp 요청 timeout 에러 발생 시

    # 300번대: Redis 관련 에러
    # REDIS_ERR = 300             # 레디스 관련 가장 상위 에러, RedisError 발생 시
    # REDIS_CONNECTION_ERR = 301  # 레디스 연결 실패 에러 발생 시

    # 기타 구분되지 않은 에러
    UNKNOWN_EXCEPTION = 999  # 정의되지 않은 에러 발생 시 (위의 모든 에러를 지나 Exception 상속 클래스일 경우)
