import json
from decimal import Decimal
from typing import Any

# NOTE: 폐기 예정 - Decimal이 아니라 string으로 넘어온다.
class KrakenDecimalJsonEncoder(json.JSONEncoder):
    """
    Decimal 객체를 문자열(str)로 변환해 JSON 직렬화 가능하게 만들기
    - 기본 설정은 str(Decimal)로 숫자형 정확도 유지 => float으로 할수있으나 정확도 유지 X => 추후 checksum 등 연산에서 실패 가능성 있음.
    """
    def default(self, obj: Any):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def decimal_json_dumps(data: Any, **kwargs) -> str:
    """
    Decimal-safe JSON 직렬화
    """
    return json.dumps(data, cls=KrakenDecimalJsonEncoder, **kwargs)


def decimal_json_loads(data: str, **kwargs) -> Any:
    """
    Decimal-safe JSON 역직렬화
    """
    return json.loads(data, parse_float=Decimal, **kwargs)
