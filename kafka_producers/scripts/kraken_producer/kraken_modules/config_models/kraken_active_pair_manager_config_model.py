from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient


class KrakenActivePairManagerConfigModel(KrakenBaseConfigModel):
    """활성화 거래쌍 관리 매니저 Config Model"""
    # Cluster IP로 배포 => K8S Dns Name => redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    redis_key: str = "kraken:active_pairs"
    component_name: str = "ACTIVE PAIR MANAGER"
    retry_num: int = 5
    retry_delay: int = 2
    conn_timeout: int = 10
