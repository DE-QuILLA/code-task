from pydantic import BaseModel

class KrakenBaseConfigModel(BaseModel):
    def get_config_dict(self) -> dict:
        """Config 모델에서 인자: 기본값 형태의 딕셔너리 반환"""
        return self.model_dump()

    def get_config_str(self) -> str:
        """Config 모델에서 딕셔너리화 => json serialized 된 string 반환"""
        return self.model_dump_json(indent=2, ensure_ascii=False)
