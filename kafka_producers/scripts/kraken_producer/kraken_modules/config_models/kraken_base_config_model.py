from pydantic import BaseModel


class KrakenRetryConfig(BaseModel):
    """네트워크 IO 등 반복 작업에 필요한 공통 설정 데이터 모델"""
    retry_num: int = 5
    retry_delay: int = 1
    conn_timeout: int = 20


class KrakenBaseConfigModel(BaseModel):
    """주요 컴포넌트 초기화 등에 사용, 객체 내부의 정보를 명세하는 데이터 모델"""
    component_name: str
    retry_config: KrakenRetryConfig = KrakenRetryConfig()

    def get_config_dict(self) -> dict:
        """Config 모델에서 인자: 값 형태의 딕셔너리 반환"""
        return self.model_dump()

    def get_config_str(self) -> str:
        """Config 모델에서 딕셔너리화 => json serialized 된 string 반환"""
        return self.model_dump_json(indent=2, ensure_ascii=False)
