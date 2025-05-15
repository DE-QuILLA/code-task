from typing import Set, Tuple, List
import asyncio
import logging
from kraken_modules.utils.logging.kraken_stdout_logger import get_start_info_msg, get_success_info_msg, get_exception_msg, get_warning_msg
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.utils.data_models.kraken_active_pair_data_model import KrakenActivePairDataModel, KrakenSubscriptionKey
from kraken_modules.interfaces.base_health_tracked_component import BaseHealthTrackedComponent


class KrakrenActivePairManager(BaseHealthTrackedComponent):
    """
    Redis에서 구독 대상 거래쌍 정보를 불러오고, 현재 상태와 비교하여 변화 추적하는 클래스
    """
    def __init__(self, redis_client: KrakenRedisClient, redis_key: str = "kraken:active_pairs", retry_num: int = 5, retry_delay: int = 2, ):
        self.redis_client = redis_client
        self.redis_key = redis_key
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.current_active_pairs: List[KrakenActivePairDataModel] = list()
        self.current_active_subscription_key: Set[KrakenSubscriptionKey] = set()
        self.logger: logging.Logger = get_stdout_logger("ACTIVE PAIR MANAGER")
        self._initialize()

    async def _initialize(self):
        """최초 상태 동기화"""
        self.logger.info(get_start_info_msg(description="활성 거래쌍 초기화",))
        init_desc_msg = "Redis에서 초기 거래쌍 로딩"
        self.refresh(logging_msg=init_desc_msg)
        self.logger.info(get_success_info_msg(description="활성 거래쌍 초기화",))

    async def refresh(self, description: str) -> Tuple[Set[str], Set[str]]:
        """
        Redis에서 최신 거래쌍을 불러오고,
        기존 거래쌍과 비교하여 (신규 구독, 구독 해제) 목록 반환

        :return: (새로운 구독할 키, 제거할 구독 키)
        """
        try:
            self.logger.info(get_start_info_msg(description="활성 거래쌍 Refresh"))
            redis_raw_data = await self._fetch_pairs_from_redis(description=description)

            redis_pairs = [KrakenActivePairDataModel(**redis_raw_pair) for redis_raw_pair in redis_raw_data]
            redis_subscription_keys = set([redis_pair.to_subscription_key() for redis_pair in redis_pairs])

            subscription_keys_to_add = redis_subscription_keys - self.current_active_subscription_key
            subscription_keys_to_delete = self.current_active_subscription_key - redis_subscription_keys

            if subscription_keys_to_add:
                self.logger.warning(get_warning_msg(description=f"새로운 구독할 거래쌍 {len(subscription_keys_to_add)}개"))
            if subscription_keys_to_delete:
                self.logger.warning(get_warning_msg(description=f"구독 취소할 거래쌍 {len(subscription_keys_to_delete)}개"))

            # 상태 업데이트
            self.current_active_pairs = redis_pairs
            self.current_active_subscription_key = redis_subscription_keys
            self.logger.info(get_success_info_msg(description="활성 거래쌍 Refresh"))
        except Exception as e:
            self.logger.exception(get_exception_msg(error=e, description="활성 거래쌍 Refresh"))
            raise e
        return subscription_keys_to_add, subscription_keys_to_delete

    async def _fetch_pairs_from_redis(self, description: str) -> Set[str]:
        """
        Redis에서 데이터를 가져오는 함수
        - 데이터를 가져오고 반환하는 역할만 수행
        """
        try:
            redis_raw_data = await custom_retry(
                logger=self.logger,
                retry_num=self.redis_client.retry_num,
                retry_delay=self.redis_client.retry_delay,
                conn_timeout=self.redis_client.conn_timeout,
                description=description,
                func=self.redis_client.redis.smembers,
                func_kwargs=self.redis_key,
            )
            return redis_raw_data
        except Exception as e:
            self.logger.exception(get_exception_msg(error=e, description="Redis에서 거래쌍 정보 읽기"))
            raise e

    def get_current_pairs(self) -> Set[str]:
        """현재 메모리에 저장된 거래쌍 반환"""
        return self.active_pairs.copy()
