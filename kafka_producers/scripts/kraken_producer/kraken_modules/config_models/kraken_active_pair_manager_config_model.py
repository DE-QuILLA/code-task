from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel, KrakenRetryConfig


class KrakenActivePairManagerConfigModel(KrakenBaseConfigModel):
    """활성화 거래쌍 관리 매니저 Config Model"""
    # Cluster IP로 배포 => K8S Dns Name => redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    # NOTE: 키 이름들은 그냥 예시, 바뀔 수 있음
    kraken_redis_key: str = "kraken:active_pairs"
    upbit_redis_key: str = "upbit:active_pairs"
    binance_redis_key: str = "binance:active_pairs"
    component_name: str = "ACTIVE PAIR MANAGER"
    retry_config: KrakenRetryConfig = KrakenRetryConfig()
