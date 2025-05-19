class KrakenBaseError(Exception):
    """
    Kraken에서 데이터를 가져오고 처리하는 과정에서 직접 정의하는 에러의 부모 클래스
    - 기본적인 동작은 에러 메시지 전달 외에 없음. 
    - 코드 내 명세화를 위한 작성
    """
    def __init__(self, message):
        super().__init__(message)

class KrakenRestApiErrorInResponseError(KrakenBaseError):
    """Kraken Rest api의 Error 필드가 빈 칸이 아닐 경우 발생하는 커스텀 Error"""
    pass

class KrakenRestApiNoDataError(KrakenBaseError):
    """Kraken Rest api의 응답 필드가 비었거나 없을 때 발생하는 커스텀 Error"""
    pass

class KrakenRestApiJsonLoadsError(KrakenBaseError):
    """Kraken Rest api의 응답을 Json load에 실패할 경우 발생하는 커스텀 Error"""
    pass

class KrakenRestApiJsonDumpsError(KrakenBaseError):
    """Kraken Rest api의 응답을 Json dumps에 실패할 경우 발생하는 커스텀 Error"""
    pass

class KrakenActivePairValueException(KrakenBaseError):
    """Kraken Rest api 응답을 파싱하는 중 잘못된 input 시 발생하는 커스텀 Exception"""
