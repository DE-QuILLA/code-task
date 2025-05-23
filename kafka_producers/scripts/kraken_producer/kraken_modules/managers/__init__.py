# init

"""
Manager 클래스(Client, 데이터 등을 관리하는 역할)를 작성하는 모듈
- KrakenActiveSymbolManager: 활성화 되어있고 내부 로직(현재 KRW, USD를 기준 통화로 하는 암호화폐)에 따라 필터링된 심볼을 관리
- KrakenProducerStatusManager: 각 컴포넌트의 헬스체크 등 상태를 관리
    - KrakenProducerComponentHealthStatus: 각 컴포넌트의 상태를 표현하는 추상화된 객체, 내부 사용
- KrakenWebSocketClientManager: channel 별로 구분되어 있는 다수의 웹소켓 클라이언트를 생성하고 관리
"""

from .kraken_active_symbol_manager import KrakenActiveSymbolManager
from .kraken_producer_status_manager import (
    KrakenProducerStatusManager,
    KrakenProducerComponentHealthStatus,
)
from .kraken_websocket_client_manager import KrakenWebSocketClientManager
