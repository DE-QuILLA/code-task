from .kraken_base_config_model import KrakenBaseConfigModel, KrakenRetryConfig


class KrakenRedisClientConfigModel(KrakenBaseConfigModel):
    """
    Redis Client Config 객체
    """

    redis_url: str = "redis.redis.svc.cluster.local"
    component_name: str = "REDIS CLIENT"


class KrakenRESTClientConfigModel(KrakenBaseConfigModel):
    """
    REST Client Config 객체
    """

    component_name: str = "REST CLIENT"
