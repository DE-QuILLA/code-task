from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from typing import Optional

class KrakenRedisClientConfigModel(KrakenBaseConfigModel):
    """활성화 거래 쌍을 가져오기 위한 Redis 연결 설정 데이터 모델"""
    status_manager: KrakenProducerStatusManager
    # Cluster IP로 배포 => K8S Dns Name => redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    redis_url: str = "redis://redis-master.redis.svc.cluster.local:6379/0"  # 예시
    retry_num: Optional[int] = 5
    retry_delay: Optional[int] = 2
    conn_timeout: Optional[int] = 10
