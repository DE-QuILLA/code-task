from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from typing import Dict, Any, Type
from abc import ABC, abstractmethod
from utils.exceptions.kraken_custom_err import KrakenRestApiErrorInResponseError, KrakenRestApiNoDataError, KrakenRestApiJsonDumpsError, KrakenRestApiJsonLoadsError
from utils.kraken_json_decimal import decimal_json_dumps, decimal_json_loads
import aiohttp
import async_timeout
import logging
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
        """"""
        raise NotImplementedError

    @abstractmethod
    def _transform(self):
        raise NotImplementedError

    @abstractmethod
    async def _load(self):
        raise NotImplementedError
    
    @abstractmethod
    async def _update_producer(self):
        raise NotImplementedError

class KrakenActivePairsRestApiCollector(KrakenBaseRestApiCollector):
    """
    크라켄에서 REST API를 기반으로 활성화된 거래쌍을 수집하여 Redis에 저장하는 Collector
    """
    def __init__(self, api_url: str, redis_url: str, redis_key: str, producer_url: str, logger: logging.Logger, params: Dict[str, Any] = None, headers: Dict[str, Any] = None, retry_num: int = 5, retry_delay: int = 5, timeout: int = 120,):
        self.api_url = api_url
        self.redis_url = redis_url
        self.redis_key = redis_key
        self.producer_url = producer_url
        self.params = params or {}
        self.headers = headers or {}
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.logger = logger

    async def run(self):
        async with aiohttp.ClientSession() as session:
            self.logger.info("크라켄 REST API에서 거래쌍 목록 불러오기 시작!")
            raw_data = await self._extract(session)
            self.logger.info("크라켄 REST API에서 거래쌍 목록 불러오기 성공!")

            self.logger.info("거래쌍 목록 처리 시작!")
            transformed_data = self._transform(raw_data)
            self.logger.info("거래쌍 목록 처리 완료!")

            self.logger.info("거래쌍 목록 Redis 저장 시작!")
            changed = await self._load(transformed_data)
            self.logger.info("거래쌍 목록 Redis 저장 완료!")

            if changed:
                self.logger.info("프로듀서에 거래쌍 변경 발생을 전달 시도 중!")
                await self._update_producer(session)
                self.logger.info("프로듀서에 거래쌍 변경 발생을 전달 완료!")
            else:
                self.logger.info("데이터 변경이 없어 작업을 종료함!")

    async def _extract(self, session: aiohttp.ClientSession):
        """크라켄 API에서 거래쌍 목록을 가져옴"""
        async with async_timeout.timeout(self.timeout):
            async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.retry_num),
                    wait=wait_fixed(self.retry_delay),
                ):
                with attempt:
                    try:
                        self.logger.info(f"{attempt.retry_state.attempt_number} 번째 연결 시도 중!")
                        async with session.get(url=self.api_url, headers=self.headers, params=self.params) as response:
                            response.raise_for_status()
                            self.logger.info(f"{self.api_url}로 연결 시도 성공!")
                    except Exception as e:
                        self._repeat_logging(attempt.retry_state.attempt_number, e, aiohttp.ClientError("크라켄 거래쌍 api 로 연결 실패!"))

                    try:
                        # 정확도, checksum 위해 Decimal로 파싱
                        response_txt = await response.text()
                        data = decimal_json_loads(response_txt)
                    except Exception as e:
                        self._repeat_logging(attempt.retry_state.attempt_number, e, KrakenRestApiJsonLoadsError("크라켄 거래쌍 api 응답 결과 Json 역직렬화 실패!"))


                    if data.get("error", []):
                        raise KrakenRestApiErrorInResponseError(f"크라켄 API로부터 에러 보고됨!: {', '.join(data.get('error', []))}")

                    if data.get("result", {}):
                        self.logger.info(f"{len(data.get('result', {}))}개 거래쌍 수집 성공!")
                        return data["result"]
                    else:
                        raise KrakenRestApiNoDataError("크라켄 API로 부터 반환된 데이터 없음!")


    def _transform(self, raw_data: Dict[str, Any]):
        """
        T 로직 사실상 없음 => 추후 거래소별 데이터 통합 구조가 결정 => redis 저장 구조를 정의 => 재구현 예정
        --------------------------------------------------------------------------------------------------------
        (추후 사용)
        status 가능한 필드와 의미
        online - 정상적으로 모든 주문 유형 가능 (시장가, 지정가 등). 일반적으로 거래 가능한 상태입니다.
        cancel_only - 신규 주문은 불가능, 기존에 제출한 주문만 취소 가능. 일시적으로 거래 제한이 있는 상태.
        post_only - 주문은 넣을 수 있지만, 시장 유동성을 제거하는 형태의 주문은 거절됨. 즉, 무조건 메이커(Maker) 주문만 가능.
        limit_only - 지정가(limit) 주문만 가능, 시장가 주문 등은 불가능.
        reduce_only - 포지션을 감소시키는 주문만 가능. 즉, 새로운 포지션 오픈은 불가능. 주로 파생상품(선물, 마진)에서 사용됨.
        """
        return raw_data

    async def _load(self, transformed_data,):
        """레디스로 데이터 적재"""
        # url 형식 = redis.default.svc.cluster.local:6379 (서비스이름.네임스페이스.svc.cluster.local:포트번호)
        redis = None  # finally의 close문 에러를 피하기 위한 초기화
        redis_url, redis_key = self.redis_url, self.redis_key
        changed = False

        async with async_timeout.timeout(self.timeout):
            async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.retry_num),
                    wait=wait_fixed(self.retry_delay),
                ):
                with attempt:
                    try:
                        self.logger.info(f"{attempt.retry_state.attempt_number} 번째 Redis 연결 시도 중!")
                        redis = aioredis.from_url(redis_url, decode_responses=True)
                        self.logger.info("Redis 연결 시도 성공!")

                        try:
                            self.logger.info("Redis 전송 데이터 직렬화 시도 중!")
                            json_data = decimal_json_dumps(transformed_data)
                            self.logger.info("Redis 전송 데이터 직렬화 완료!")
                        except Exception as e:
                            self._repeat_logging(attempt.retry_state.attempt_number, e, KrakenRestApiJsonDumpsError("크라켄 거래쌍 api 응답 데이터 Redis 전송하기 위한 json 직렬화 실패!"))
                        
                        try:
                            self.logger.info("Redis 데이터와 상태 비교 중!")
                            current = await redis.get(redis_key)
                            if current != json_data:
                                changed = True
                                self.logger.info("Redis 데이터와 상태 다름! Redis로 데이터를 저장함!")
                            else:
                                self.logger.info("Redis 데이터와 상태 같음. Redis로 데이터를 저장하지 않음!")
                        except Exception as e:
                            self._repeat_logging(attempt.retry_state.attempt_number, e, aioredis.RedisError("Redis에서 이전 거래쌍 데이터 읽어오는 과정 실패!"))

                        try:
                            if changed:
                                self.logger.info(f"{len(transformed_data)}개 항목 redis로 저장 시작!")
                                await redis.set(redis_key, json_data)
                                self.logger.info(f"Redis에 '{redis_key}' 키로 거래쌍 저장 완료!")
                            else:
                                self.logger.info(f"Redis로 데이터 저장 과정 생략됨!")
                        except Exception:
                            self._repeat_logging(attempt.retry_state.attempt_number, aioredis.RedisError("Redis에 크라켄 거래쌍 정보 송신 실패!"))

                    except Exception as e:
                        self._repeat_logging(attempt.retry_state.attempt_number, e, aioredis.ConnectionError("Redis 연결 실패!"))
                    finally:
                        if redis:
                            await redis.close()
        return changed

    async def _update_producer(self, session: aiohttp.ClientSession):
        async with async_timeout.timeout(self.timeout):
            async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.retry_num),
                    wait=wait_fixed(self.retry_delay),
                ):
                try:
                    self.logger.info(f"{self.producer_url}로 연결 및 변경 사항 프로듀서 api 호출 중!")
                    async with session.post(self.producer_url, json={"changed": True}) as response:
                        response.raise_for_status()
                    self.logger.info(f"연결 및 변경 사항 프로듀서 api 전달 성공!")
                except Exception as e:
                    self._repeat_logging(attempt.retry_state.attempt_number, e, aiohttp.ClientError("변경 사항 프로듀서 api로 전달 실패!"))

    def _repeat_logging(self, current_attempt_count: int, error_object: Exception, throw_err_class: Type[Exception]):
        if current_attempt_count < self.retry_num:
            self.logger.warning(f"\n{current_attempt_count} 번째 시도 실패 - {type(error_object).__name__}: {error_object}\n")
        else:
            raise throw_err_class(str(error_object)) from error_object
