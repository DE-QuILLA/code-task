from pydantic import BaseModel
from abc import ABC, abstractmethod
import json
from typing import Dict, Optional, List, Any
from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager


class KrakenBaseWebSocketClientConfigModel(KrakenBaseConfigModel, ABC):
    """Kraken 웹소켓 설정용 공통 데이터 모델 추상 클래스"""
    # 구독관련 설정 - 채널마다 오버라이드
    url: str
    channel: str
    symbol: Optional[List[str]]
    snapshot: Optional[bool] = True

    # 아래는 공통 설정들
    topic_name: str
    retry_num: Optional[int] = 5
    retry_delay: Optional[int] = 1
    conn_timeout: Optional[int] = 20

    @abstractmethod
    def _params(self) -> Dict[str, Any]:
        raise NotImplementedError

    @property
    def subscription_msg(self) -> Dict[str, Any]:
        """구독 메시지 반환"""
        return json.dumps({
            "method": "subscribe",
            "params": self._params()
        })
    
    # TODO: API 명세 확인하고 수정해야함.
    @property
    def unsubscription_msg(self) -> Dict[str, Any]:
        return json.dumps({
            "mehtod": "unsubscribe",
            "params": self._params()
        })


class KrakenTickerWebSocketClientConfigModel(KrakenBaseWebSocketClientConfigModel):
    """Ticker 채널 구독용 설정 데이터 모델 - 거래쌍 별 기본 정보 조회"""
    # 구독용 설정
    url: str = "wss://ws.kraken.com/v2"
    channel: str = "ticker"
    symbol: List[str] = []
    event_trigger: str = "trades"  # bbo / trades 선택 가능 각각 best-bid-offer price 변경 / 거래 발생
    snapshot: bool = True

    topic_name: str = "kraken:ticker"

    def _params(self) -> Dict[str, Any]:
        """Ticker 구독 메시지 params 반환"""
        ticker_params = {
                "channel": self.channel,
                "symbol": self.symbol,
                "evnet_trigger": self.event_trigger,
                "snapshot": self.snapshot,
            }
        return ticker_params



class KrakenBookWebSocketClientConfigModel(KrakenBaseWebSocketClientConfigModel):
    """Book 채널 구독용 설정 데이터 모델 - 거래쌍 별 호가창 조회"""
    url: str = "wss://ws.kraken.com/v2"
    channel: str = "book"
    symbol: List[str] = []
    depth: int = 10  # 호가창 구분 개수를 의미, 가능한 값: [10, 25, 100, 500, 1000], 기본 10
    snapshot: bool = True

    topic_name: str = "kraken:book"

    def _params(self) -> Dict[str, Any]:
        """Book 구독 메시지 params 반환"""
        book_params = {
                "channel": self.channel,
                "symbol": self.symbol,
                "depth": self.depth,
                "snapshot": self.snapshot,
        }
        return book_params


class KrakenCandleWebSocketClientConfigModel(KrakenBaseWebSocketClientConfigModel):
    """Candle 채널 구독용 설정 데이터 모델 - 거래쌍 별 분봉 조회"""
    url: str = "wss://ws.kraken.com/v2"
    channel: str = "ohlc"
    symbol: List[str] = []
    interval: int = 1  # 캔들의 시간 단위를 의미, 가능한 값: [1, 5, 15, 30, 60, 240, 1440, 10080, 21600] => 분단위
    snapshot: bool = True
    
    topic_name: str = "kraken:ohlc"

    def _params(self) -> Dict[str, Any]:
        """Candle 구독 메시지 params 반환"""
        candle_params = {
                "channel": self.channel,
                "symbol": self.symbol,
                "interval": self.interval,
                "snapshot": self.snapshot,
        }
        return candle_params


class KrakenTradeWebSocketClientConfigModel(KrakenBaseWebSocketClientConfigModel):
    """Trade 채널 구독용 설정 데이터 모델 - 거래쌍 별 거래 트랜잭션 조회"""
    url: str = "wss://ws.kraken.com/v2"
    channel: str = "trade"
    symbol: List[str] = []
    snapshot: bool = True

    topic_name: str = "kraken:trade"
    
    def _params(self) -> Dict:
        """Trade 구독 메시지 params 반환"""
        trade_params = {
                "channel": self.channel,
                "symbol": self.symbol,
                "snapshot": self.snapshot,
        }
        return trade_params
    

class KrakenPingWebSocketClientConfigModel(KrakenBaseWebSocketClientConfigModel):
    """PING 채널을 통해 연결이 살아있는지 확인하는 데에 사용"""
    url: str = "wss://ws.kraken.com/v2"
    channel: str = "ping"

    def _params(self) -> Dict[str, Any]:
        pass

    @property
    def subscription_msg(self) -> Dict[str, Any]:
        """구독 메시지 반환"""
        return {
            "method": "ping",
        }



# 아래를 import 하여 동적으로 웹소켓 클라이언트 개수 조절
ALL_WEBSOCKET_CLIENT_CONFIG_MODELS = [KrakenTickerWebSocketClientConfigModel, KrakenBookWebSocketClientConfigModel, KrakenCandleWebSocketClientConfigModel, KrakenTradeWebSocketClientConfigModel]
