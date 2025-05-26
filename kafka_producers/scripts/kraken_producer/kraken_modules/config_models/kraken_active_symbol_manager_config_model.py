from kraken_modules.config_models import KrakenBaseConfigModel, KrakenRetryConfig


class KrakenActiveSymbolManagerConfigModel(KrakenBaseConfigModel):
    """활성화 거래쌍 관리 매니저 Config Model"""

    # Cluster IP로 배포 => K8S Dns Name => redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    # NOTE: 키 이름들은 그냥 예시, 바뀔 수 있음
    kraken_redis_key: str = "symbol:kraken:base"
    upbit_redis_key: str = "symbol:upbit:base"
    binance_redis_key: str = "symbol:binance:base"
    common_redis_key: str = "symbol:common:base"
    component_name: str = "ACTIVE PAIR MANAGER"
    retry_config: KrakenRetryConfig = KrakenRetryConfig()
