from pydantic import BaseModel


class KrakenRetryConfig(
    BaseModel,
):
    """
    재시도 관련 Config 객체
    """

    retry_num: int = 5
    retry_delay: int = 1
    conn_timeout: int = 20


class KrakenBaseConfigModel(
    BaseModel,
):
    """
    모든 주요 컴포넌트 초기화 값을 담는 Config 객체
    """

    retry_num: int = 5
    retry_delay: int = 1
    conn_timeout: int = 20
    retry_config: KrakenRetryConfig = KrakenRetryConfig(
        retry_num=retry_num, retry_delay=retry_delay, conn_timeout=conn_timeout
    )

    def get_config_dict(self) -> dict:
        """Config 모델에서 인자: 값 형태의 딕셔너리 반환"""
        return self.model_dump()

    def get_config_str(self) -> str:
        """Config 모델에서 딕셔너리화 => json serialized 된 string 반환"""
        return self.model_dump_json(indent=2, ensure_ascii=False)
