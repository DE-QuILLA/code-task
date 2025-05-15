from pydantic import BaseModel
from abc import ABC, abstractmethod
from redis.asyncio import Redis
from typing import Optional, Dict


class KrakenBaseRedisClientConfigModel(BaseModel, ABC):
    """Kraken 데이터 Prodcuer Redis 연결 설정을 관리하는 데이터 모델 추상 클래스"""
    redis_url: str
    retry_num: Optional[int]
    retry_delay: Optional[int]
    conn_timeout: Optional[int]

    @abstractmethod
    @property
    def params(self) -> Dict:
        raise NotImplementedError


class KrakenActivePairRedisClientConfigModel(KrakenBaseRedisClientConfigModel):
    """활성화 거래 쌍을 가져오기 위한 Redis 연결 설정 데이터 모델"""
    # Cluster IP로 배포 => K8S Dns Name => redis://<release-name>-master.<namespace>.svc.cluster.local:<port>/0
    redis_url: str = "redis://redis-master.redis.svc.cluster.local:6379/0"
    retry_num: int = 5
    retry_delay: int = 2
    conn_timeout: int = 10

    @property
    def input_params(self) -> Dict:
        """활성화 거래 쌍 용 RedisClient 객체 초기화 input 리턴"""
        return {
            "redis_url": self.redis_url,
            "retry_num": self.retry_num,
            "retry_delay": self.retry_delay,
            "conn_timeout": self.conn_timeout,
        }
