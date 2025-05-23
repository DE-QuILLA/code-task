# libraries
from aiohttp import ClientSession
from typing import Dict, Any, Set
from abc import ABC, abstractmethod

# custom
from kraken_modules.utils.exceptions import (
    KrakenErrorInAPIResponseException,
    KrakenAPIResponseNoDataException,
    KrakenAPIResponseValueException,
    KrakenProducerAPICallFailException,
)
from kraken_modules.utils.logging import KrakenStdandardLogger
from kraken_modules.utils.wrappers import custom_retry
from kraken_modules.clients import KrakenRedisClient
from kraken_modules.clients import KrakenRESTClient
from kraken_modules.config_models import KrakenRESTAPICollectorConfigModel


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


class KrakenActiveSymbolsRestApiCollector(KrakenBaseRestApiCollector):
    """
    크라켄에서 REST API를 기반으로 활성화된 거래쌍을 수집하여 Redis에 저장하는 Collector
    """

    def __init__(
        self,
        config: KrakenRESTAPICollectorConfigModel,
        redis_client: KrakenRedisClient,
        rest_client: KrakenRESTClient,
    ):
        # config 저장
        self.config = config

        # 외부객체
        self.redis_client: KrakenRedisClient = redis_client
        self.rest_client: KrakenRESTClient = rest_client
        self.logger = KrakenStdandardLogger(logger_name=self.config.component_name)

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

    async def _extract(
        self,
    ):
        """
        크라켄 API에서 거래쌍 목록을 가져옴
        """
        raw_data = await self.rest_client.fetch(
            path="some_path",
            headers=self.config.api_headers,
            params=self.config.api_params,
        )

        if raw_data.get("error", []):
            e = KrakenErrorInAPIResponseException(
                f"Kraken API Error 응답: {', '.join(raw_data['error'])}"
            )
            self.logger.exception_common(error=e, description="크라켄 활성 symbol 수집")
            raise e

        if raw_data.get("result", {}):
            self.logger.info_success(f"{len(raw_data.get('result', {}))}개 거래쌍 수집")
            return raw_data["result"]
        else:
            self.logger.warning_common(
                description=f"비어있는 API 응답 데이터",
            )
            raise KrakenAPIResponseNoDataException("Kraken API 비어있는 응답 발생")

    def _transform(self, raw_data: Dict[str, Any]) -> Set[str]:
        """
        불러온 데이터를 파싱, 아래 기준으로 필터링 => symbol의 Set[str] 형태로 반환
        - status 필드가 online(정상 거래 가능)
        - 기준 통화가 USD 혹은 KRW인 경우
        """
        self.logger.info_start(f"{len(raw_data)} 거래쌍 심볼 transform")
        krw_base_pairs = set()
        usd_base_pairs = set()

        for k, v in raw_data.items():
            try:
                wsname: str = v["wsname"]
                base, quote = wsname.split("/")  # 예시: base = BTC, quote = USD
                status: str = v["status"]

                # 혹시나 Upper로 바꾸기
                wsname = wsname.upper()
                base, quote = base.upper(), quote.upper()
            except (KeyError, ValueError) as e:
                self.logger.exception_common(f"활성 Symbol 처리")
                raise KrakenAPIResponseValueException(
                    f"wsname, status 정보 처리 중 예외 발생\n{k} : {v}"
                )
            except Exception as e:
                self.logger.exception_common(f"활성 Symbol 처리")
                raise

            if quote in ("KRW", "USD") and status == "online":
                if quote == "KRW":
                    self.logger.logger.info(f"KRW 기준 활성 거래쌍: {wsname}")
                    krw_base_pairs.add(base)
                else:
                    self.logger.logger.info(f"USD 기준 활성 거래쌍: {wsname}")
                    usd_base_pairs.add(base)
            else:
                self.logger.logger.info(
                    f"KRW/USD 기준 통화가 아니거나 online 상태가 아닌 거래쌍: {wsname}"
                )

        result = krw_base_pairs & usd_base_pairs
        self.logger.info_success(f"{len(result)} 개 활성 symbol 처리")
        return result

    async def _load(self, transformed_data: Set[str]):
        """
        적재 로직, Redis Client에서 변화가 있는지 확인하여 적재, 변화가 발생 시 True, 아닐 시 False 리턴
        """
        changed_flag = await self.redis_client.update_if_changed(
            redis_key=self.config.kraken_redis_key, new_data=transformed_data
        )
        return changed_flag

    async def _update_producer(
        self,
    ):
        """
        Redis 단에 변경 발생시 실행, Producer의 api /reload 엔드포인트 호출하여 심볼 reload 지시
        """
        fail_urls = []
        async with ClientSession() as session:
            # NOTE: producer_url 초기화 시 "http://<host>:<port>/reload" 형식이 되어야 함에 주의(엔드포인트 포함)
            for producer_url in self.config.producer_urls:
                try:
                    await custom_retry(
                        logger=self.logger,
                        retry_config=self.config.retry_config,
                        description="Kraken Producer /reload 호출",
                        func=lambda: session.post(
                            producer_url, json={"changed": "kraken"}
                        ),
                        func_kwargs=None,
                    )
                except Exception as e:
                    fail_urls.append(producer_url)

            if len(fail_urls) > 0:
                raise KrakenProducerAPICallFailException(
                    f"[{', '.join(fail_urls)}] ({len(fail_urls)} 개) 호출 실패"
                )
