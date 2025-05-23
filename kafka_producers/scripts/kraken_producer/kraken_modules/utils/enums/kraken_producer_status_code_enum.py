from enum import Enum


class KrakenProducerStatusCodeEnum(Enum):
    """
    전체 컴포넌트에서 공통적으로 사용할 status code 정의
    - 0: 아직 제대로 시작되지 않음. 초기화에 사용
    - 양수: 제대로 동작 중인 상태
    - 음수: 문제가 있는 상태 구분
    """

    # 0. 초기화되지 않음.
    NOT_STARTED = 0  # 비동기 등으로 아직 제대로 초기화 되지 않음

    # 1. 정상적으로 작동 중
    STARTED = 1  # 제대로 초기화 되어 정상적으로 실행된 상태

    # 2. 세션이 닫히는 등 리소스 정리 후
    HEALTHY_EXIT = 2

    ##
    # -1. 알수 없는 에러 발생(로그 확인)
    ERROR = -1

    # -2. 상태 관리 관련 잘못된 input 발생
    NOT_VALID_STATUS_INPUT = -2

    # -3. (CLIENT) 연결 실패
    CLIENT_FAIL_TO_CONNECT = -3

    # -4. Data 없음
    NO_DATA = -4

    # -5. (매니저 객체들) 관리할 객체 없음
    NO_OBJECT_TO_MANAGE = -5

    # -6. 헬스체크 정보 수신되지 않음(웹소켓 heartbeat)
    NO_HEART_BEAT = -6
