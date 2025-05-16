from abc import ABC

class KrakenProducerBaseException(Exception):
    """
    Kraken에서 데이터를 가져오고 처리하는 Producer에서 직접 정의하는 에러의 부모 클래스
    - 기본적인 동작은 에러 메시지 전달 외에 없음. 
    - 코드 내 명세화를 위한 작성
    """
    def __init__(self, message):
        super().__init__(message)

class KrakenProducerKafkaClientException(KrakenProducerBaseException):
    """Kafka 연결 실패 시 발생하는 에러"""
    pass

class KrakenProdcuerRedisConnectionException(KrakenProducerBaseException):
    """Redis 연결 실패 시 발생 에러"""
    pass

class KrakenProdcuerActivePairTypeException(KrakenProducerBaseException):
    """활성화 거래쌍의 데이터 타입 에러"""
    pass

class KrakenProducerNotValidStatusCodeException(KrakenProducerBaseException):
    """존재하지 않는 상태 코드 인풋 에러"""
    pass

class KrakenProducerNotValidMessageTypeException(KrakenProducerBaseException):
    """Dict 혹은 str이 아닌 메시지 발생"""
    pass