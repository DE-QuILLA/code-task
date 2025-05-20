from typing import Dict, Any, Type, List, Set
from abc import ABC, abstractmethod
from kraken_modules.utils.exceptions.kraken_custom_err import KrakenRestApiErrorInResponseError, KrakenRestApiNoDataError
from kraken_modules.utils.data_models.kraken_active_pair_data_models import KrakenActivePairDataModel
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.wrappers.custrom_retry_wrapper import custom_retry
from kraken_modules.clients.kraken_redis_client import KrakenRedisClient
from kraken_modules.clients.kraken_rest_client import KrakenRestClient
from kraken_modules.utils.data_models.kraken_active_pair_data_models import KrakenActiveSymbol
from aiohttp import ClientSession
import redis.asyncio as aioredis


class KrakenBaseRestApiCollector(ABC):
    """
    크라켄 관련 rest api 기반 데이터 수집 추상클래스
    """
    def __init__(self):
        pass
    
    @abstractmethod
    async def run(self):
        """
        데이터 수집 동작 명세 작성
        - ETL 혹은 ELT 순서 가정하여 각 함수 순서대로 호출
        - 각 단계 사이의 스텝 정의
        """
        raise NotImplementedError
    
    @abstractmethod
    async def _extract(self):
        """Extract 관련 로직 작성"""
        raise NotImplementedError

    @abstractmethod
    def _transform(self):
        """Transform 관련 로직 작성"""
        raise NotImplementedError

    @abstractmethod
    async def _load(self):
        """Load 관련 로직 작성"""
        raise NotImplementedError
    
    @abstractmethod
    async def _update_producer(self):
        """필요할 경우 Producer 상태 갱신 요청 보내는 로직 작성"""
        raise NotImplementedError


class KrakenActivePairsRestApiCollector(KrakenBaseRestApiCollector):
    """
    크라켄에서 REST API를 기반으로 활성화된 거래쌍을 수집하여 Redis에 저장하는 Collector
    """
    def __init__(self, api_url: str, redis_url: str, redis_key: str, producer_url: str, api_params: Dict[str, Any] = None, api_headers: Dict[str, Any] = None, retry_num: int = 5, retry_delay: int = 2, conn_timeout: int = 20,):
        self.api_url = api_url
        self.redis_url = redis_url
        self.redis_key = redis_key
        self.producer_url = producer_url
        self.api_params = api_params or {}
        self.api_headers = api_headers or {}
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.conn_timeout = conn_timeout
        self.logger = KrakenStdandardLogger("KRAKEN ACTIVE PAIR REST API COLLECTOR")

        self._initialize()

    def _initialize(self,):
        self.redis_client = KrakenRedisClient(redis_url=self.redis_url, )
        self.rest_client = KrakenRestClient(base_url=self.api_url, headers=self.api_headers,)

    async def run(self):
        self.logger.info_start("거래쌍 목록 INGESTION")
        raw_data = await self._extract()
        self.logger.info_success("거래쌍 목록 INGESTION")

        self.logger.info_start("거래쌍 목록 TRANSFORMATION")
        transformed_data = self._transform(raw_data)
        self.logger.info_success("거래쌍 목록 TRANSFORMATION")

        self.logger.info_start("거래쌍 목록 LOAD (Redis)")
        changed_flag = await self._load(transformed_data)
        self.logger.info_start("거래쌍 목록 LOAD (Redis)")

        if changed_flag:
            self.logger.info_start("프로듀서 /reload 호출")
            await self._update_producer()
            self.logger.info_success("프로듀서 /reload 호출")
        else:
            self.logger.info_start("데이터 변경 감지되지 않아 작업 종료")

    async def _extract(self, ):
        """크라켄 API에서 거래쌍 목록을 가져옴"""
        raw_data = await self.rest_client.fetch(path="some_path", params=self.api_params,)

        if raw_data.get("error", []):
            self.logger.exception_common(error=KrakenRestApiErrorInResponseError, desc="크라켄 거래쌍 API ERROR 반환")
            raise KrakenRestApiErrorInResponseError(f"크라켄 거래쌍 API로부터 에러 보고됨!: {', '.join(raw_data.get('error', []))}")

        if raw_data.get("result", {}):
            self.logger.info_success(f"{len(raw_data.get('result', {}))}개 거래쌍 수집")
            return raw_data["result"]
        else:
            self.logger.warning_common(desc=f"크라켄 거래쌍 API 데이터 반환하지 않음",)
            raise KrakenRestApiNoDataError("크라켄 거래상 API로 부터 반환된 데이터 없음!")

    def _transform(self, raw_data: Dict[str, Any]) -> Set[str]:
        """
        불러온 데이터를 간단히 파싱하여 아래와 같이 필터링하여 symbol 형태로 반환함
        - status 필드가 online(정상 거래 가능)
        - 기준 통화가 USD 혹은 KRW인 경우
        """
        krw_base_pairs = set()
        usd_base_pairs = set()

        for k, v in raw_data.items():
            wsname: str = v["wsname"]
            base, quote = wsname.split("/")  # 예시: base = BTC, quote = USD
            status: str = v["status"]
            
            if quote in ("KRW", "USD") and status == "online":
                if quote == "KRW":
                    krw_base_pairs.add(base)
                else:
                    usd_base_pairs.add(base)
            else:
                self.logger.warning_common("KRW/USD가 아니거나 status가 online이 아닌 데이터")

        return krw_base_pairs & usd_base_pairs


    async def _load(self, transformed_data: Set[str]):
        changed_flag = await self.redis_client.update_if_changed(redis_key=self.redis_key, new_data=transformed_data)
        return changed_flag


    async def _update_producer(self,):
        async with ClientSession() as session:
            await custom_retry(
                logger=self.logger,
                retry_num=self.retry_num,
                retry_delay=self.retry_delay,
                conn_timeout=self.conn_timeout,
                description="Kraken Producer /reload 호출",
                func=lambda: session.post(self.producer_url, json={"changed": True}),
                func_kwargs=None,
            )
