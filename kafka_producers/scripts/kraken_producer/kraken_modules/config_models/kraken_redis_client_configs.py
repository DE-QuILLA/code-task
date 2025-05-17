from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from typing import Optional

class KrakenRedisClientConfigModel(KrakenBaseConfigModel):
    """활성화 거래 쌍을 가져오기 위한 Redis 연결 설정 데이터 모델"""
    # Cluster IP로 배포 => K8S Dns Name => 예: redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    # NOTE: 예시, 수정 가능성 있음
    redis_url: str = "redis://redis-master.redis.svc.cluster.local:6379/0"
    retry_num: Optional[int] = 5
    retry_delay: Optional[int] = 2
    conn_timeout: Optional[int] = 10
    component_name: str = "REDIS CLIENT"
