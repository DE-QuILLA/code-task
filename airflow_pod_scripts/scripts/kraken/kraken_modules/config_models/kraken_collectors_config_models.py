from .kraken_base_config_model import KrakenRetryConfig, KrakenBaseConfigModel
from typing import Dict, Any, List


class KrakenRESTAPICollectorConfigModel(KrakenBaseConfigModel):
    """
    Collector Config 객체
    """

    component_name: str = "REST API ACTIVE SYMBOL COLLECTOR"

    api_url: str = "https://api.kraken.com/0/public/Assets"
    kraken_symbol_redis_key: str = "symbol:kraken:base"
    upbit_symbol_redis_key: str = "symbol:upbit:base"
    binance_symbol_redis_key: str = "symbol:binance:base"
    common_symbol_redis_key: str = "symbol:common:base"
    kraken_symbol_meta_redis_key: str = "symbol:kraken:fee"  # NOTE: 바뀌거나 사용되지 않을 예정 있음.
    producer_urls: List[str]
    api_params: Dict[str, Any] = {}
    api_headers: Dict[str, Any] = {}

    @property
    def redis_keys_of_symbols(self,):
        return [self.kraken_symbol_redis_key, self.binance_symbol_redis_key, self.upbit_symbol_redis_key]

# 
# 
# 
# 