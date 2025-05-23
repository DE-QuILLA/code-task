from .kraken_base_config_model import KrakenRetryConfig, KrakenBaseConfigModel
from typing import Dict, Any, List


class KrakenRESTAPICollectorConfigModel(KrakenBaseConfigModel):
    """
    Collector Config 객체
    """

    component_name: str = "REST API ACTIVE SYMBOL COLLECTOR"

    api_url: str = "https://api.kraken.com/0/public/Assets"
    kraken_redis_key: str = "kraken_base_symbols"
    producer_urls: List[str]
    api_params: Dict[str, Any] = {}
    api_headers: Dict[str, Any] = {}
