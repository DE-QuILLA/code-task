from enum import Enum

class KrakenProducerStatusCodeEnum(Enum):
    """전체 서비스에서 공통적으로 사용할 status code 정의"""
    # 0. 초기화되지 않음.
    NOT_STARTED = 0  # 비동기 등으로 아직 제대로 초기화 되지 않음

    # 1. 정상적으로 작동 중
    STARTED = 1      # 제대로 초기화 되어 정상적으로 실행된 상태

    # 2. 세션이 닫히는 등 리소스 정리 후
    HEALTHY_EXIT = 2
    
    # 3. 스테이터스 코드 입력 실패
    NOT_VALID_STATUS_CODE = 3

    # -1. 에러 발생
    ERROR = -1
