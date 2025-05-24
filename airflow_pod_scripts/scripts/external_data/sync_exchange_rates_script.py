# custom
from external_data_modules.logging import StdandardLogger

# libraries
import argparse
import asyncio
import aiohttp
import json
from decimal import Decimal, InvalidOperation
from redis.asyncio import Redis
from typing import Dict, Any
from argparse import Namespace
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type



@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception)
)
async def get_exchange_rate(
    logger: StdandardLogger,
    session: aiohttp.ClientSession,
    base_url: str,
    api_key: str,
    base: str,
    target: str
) -> str:
    url = f"{base_url}?api_key={api_key}&base={base}&currencies={target}"
    logger.info_start(description=f"[{url}] 로 부터 데이터 ingestion")
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data: Dict[str, Any] = await resp.json()

            if data.get("success", None) and target in data["rates"]:
                result = str(data["rates"][target])
                logger.info_success(description=f"[{url}] 로 부터 데이터 ingestion")
                return result
            else:
                raise ValueError(f"API 응답 이상: \n{data}")
    except Exception as e:
        logger.exception_common(error=e, description=f"[{url}] 로 부터 데이터 ingestion")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception)
)
async def fetch_and_store_rates(
    logger: StdandardLogger,
    redis: Redis,
    redis_key: str,
    base_url: str,
    api_key: str
) -> Dict[str, str]:
    async with aiohttp.ClientSession() as session:
        usd_to_krw = await get_exchange_rate(logger=logger, session=session, base_url=base_url, api_key=api_key, base="USD", target="KRW",)

        try:
            krw_to_usd = str(Decimal("1") / Decimal(usd_to_krw))
        except Exception as e:
            logger.exception_common(error=e, description="KRW to USD 환율 계산")
            raise

        rates = {
            "USD_KRW": str(usd_to_krw),
            "KRW_USD": str(krw_to_usd),
        }
        logger.warning_common(f"저장할 환율 데이터: \n{rates}\n")

        try:
            logger.info_start(f"Redis에 데이터 저장")
            await redis.set(redis_key, json.dumps(rates),)
            logger.info_success(f"Redis에 데이터 저장")
            return rates
        except Exception as e:
            logger.exception_common(error=e, description=f"redis에 데이터 저장")
            raise


async def main():
    logger = StdandardLogger(logger_name="EXCHANGE RATE COLLECTOR")

    logger.info_start(description="argument parsing")
    parser = argparse.ArgumentParser(
            description="환율 데이터 동기화 스크립트 argument parser"
        )

    parser.add_argument(
        "--api_url", type=str, required=True, help="Forex 실시간 환율 API URL",
    )
    parser.add_argument(
        "--api_key", type=str, required=True, help="Forex API KEY",
    )
    parser.add_argument(
        "--redis_url", type=str, required=True, help="GKE 내 Redis Service URL",
    )
    parser.add_argument(
        "--redis_key", type=str, required=True, help="환율 정보를 캐싱할 Redis 내의 key",
    )
    args: Namespace = parser.parse_args()
    api_url = args.api_url
    api_key = args.api_key
    redis_url = args.redis_url
    redis_key = args.redis_key
    logger.info_success(description="argument parsing")

    redis = Redis(host=redis_url, port=6379, decode_responses=True)
    try:
        rates: Dict[str, str] = await fetch_and_store_rates(logger=logger, redis=redis, redis_key=redis_key, base_url=api_url, api_key=api_key,)
        logger.info_success(f"[{', '.join([f"{k}: {v}" for k, v in rates.items()])}] 환율 정보 저장")
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
