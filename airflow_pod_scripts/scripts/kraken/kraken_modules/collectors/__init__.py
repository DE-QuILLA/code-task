# init

"""
ETL 로직을 담당하는 Collector 클래스들의 모듈
- KrakenBaseRestApiCollecotr: REST API로 부터 데이터를 수집하는 기능을 표현하는 추상 클래스
- KrakenActiveSymbolsRestApiCollector: 활성화되어있는 Symbol을 수집하고 Redis 갱신하는 클래스
"""

from .kraken_rest_api_collector import KrakenBaseRestApiCollector
from .kraken_rest_api_collector import KrakenActiveSymbolsRestApiCollector
