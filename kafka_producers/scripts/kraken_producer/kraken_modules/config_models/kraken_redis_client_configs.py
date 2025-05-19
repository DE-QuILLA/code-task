from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel, KrakenRetryConfig


class KrakenRedisClientConfigModel(KrakenBaseConfigModel):
    """활성화 거래 쌍을 가져오기 위한 Redis 연결 설정 데이터 모델"""
    # NOTE: url은 우선 예시, Cluster IP로 배포 => K8S Dns Name => 예: redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    redis_url: str = "redis://redis-master.redis.svc.cluster.local:6379/0"
    component_name: str = "REDIS CLIENT"
    retry_config: KrakenRetryConfig = KrakenRetryConfig()
