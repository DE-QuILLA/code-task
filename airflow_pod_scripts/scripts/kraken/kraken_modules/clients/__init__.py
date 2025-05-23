# init

"""
Redis, REST API 등 외부 커넥션을 나타내는 객체 모듈
- KrakenRedisClient: Redis
- KrakenRestClient: 크라켄 REST API
"""

# 1. Redis Client
from .kraken_redis_client import KrakenRedisClient

# 2. REST API Client
from .kraken_rest_client import KrakenRESTClient
