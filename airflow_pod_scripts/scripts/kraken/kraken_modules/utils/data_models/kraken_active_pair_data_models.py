from decimal import Decimal
from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, field_validator

class KrakenSubscriptionKey(BaseModel):
    class Config:
        frozen = True

    wsname: str
    status: Literal["online", "cancel_only", "post_only", "limit_only", "disabled"]


class KrakenActivePairDataModel(BaseModel):
    altname: str  # 내부 거래쌍 명 (예: 1INCHEUR)
    wsname: str   # 외부 표기명, 웹소켓 구독에 사용 (예: 1INCH/EUR)
    
    aclass_base: str   # 기준 자산의 자산 클래스 (보통 "currency")
    base: str          # 기준 자산 (예: "1INCH")
    aclass_quote: str  # 상대 자산의 자산 클래스 (보통 "currency")
    lot: str           # 주문 단위 (예: "unit")

    cost_decimals: int   # 총 비용 표시 소수점 자리수
    pair_decimals: int   # 가격 표시 소수점 자리수
    lot_decimals: int    # 수량 표시 소수점 자리수
    lot_multiplier: int  # 주문 최소 단위 배수

    leverage_buy: List[int]   # 매수 레버리지 지원 단계
    leverage_sell: List[int]  # 매도 레버리지 지원 단계

    fees: List[List[Decimal]]                         #  일반 수수료 계층 [[거래량, 수수료]]
    fees_maker: Optional[List[List[Decimal]]] = None  # 메이커 수수료 계층
    fee_volume_currency: Optional[str] = None         # 수수료 거래량 기준 통화

    margin_call: Optional[int] = 0  # 마진콜 비율 (%)
    margin_stop: Optional[int] = 0  # 마진 정지 비율 (%)
    
    ordermin: Decimal                    # 최소 주문 수량
    costmin: Optional[Decimal] = None    # 최소 주문 비용    
    tick_size: Optional[Decimal] = None  # 가격 단위 간격
    status: Literal["online", "cancel_only", "post_only", "limit_only", "disabled"]  # 거래쌍 상태

    def to_subscription_key(self) -> KrakenSubscriptionKey:
        """subscription key가 될 객체를 반환함"""
        return KrakenSubscriptionKey(wsname=self.wsname, status=self.status)

    @field_validator("ordermin", "costmin", "tick_size", mode="before")
    @classmethod
    def parse_decimal_fields(cls, v, info):
        try:
            return Decimal(v) if v is not None else None
        except Exception as e:
            raise e(
                f"[{info.field_name}] Decimal(Decimal, Optional[Decimal]) 변환 실패, 값: {v}, 에러: ({type(e).__name__} - {e})"
            )

    @field_validator("fees", "fees_maker", mode="before")
    @classmethod
    def parse_fee_table(cls, v, info):
        if v is None:
            return None
        try:
            return [[Decimal(i) for i in sub] for sub in v]
        except Exception as e:
            raise e(
                f"[{info.field_name}] 수수료 테이블(List[List[Decimal]]) 변환 실패, 값: {v}, 에러: ({type(e).__name__} - {e})"
            )

    @field_validator("margin_call", "margin_stop", mode="before")
    @classmethod
    def parse_margin_fields(cls, v, info):
        if v in (None, "", "0"):
            return None
        try:
            return int(v)
        except Exception as e:
            raise e(
                f"[{info.field_name}] margin 필드 정수(Optional[int]) 변환 실패, 값: {v}, 에러: ({type(e).__name__} - {e})"
            )

    @field_validator("leverage_buy", "leverage_sell", mode="before")
    @classmethod
    def parse_leverage(cls, v, info):
        try:
            return [int(i) for i in v]
        except Exception as e:
            raise e(
                f"[{info.field_name}] 레버리지 리스트(List[int]) 변환 실패, 값: {v} 에러: ({type(e).__name__} - {e})"
            )


class KrakenActiveSymbol(BaseModel):
    """KRW, USD로 모두 거래 가능하며, 상태가 online인 심볼을 표현하는 데이터 모델"""
    symbol: str
    status: str = "online"

    @field_validator("status", mode="before")
    @classmethod
    def status_validator(cls, value):
        if value != "online":
            raise

