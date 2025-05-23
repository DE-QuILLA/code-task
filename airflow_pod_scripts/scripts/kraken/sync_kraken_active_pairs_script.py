# custom
from kraken_modules.collectors import KrakenActiveSymbolsRestApiCollector
from kraken_modules.clients import KrakenRedisClient, KrakenRESTClient
from kraken_modules.config_models import (
    KrakenRedisClientConfigModel,
    KrakenRESTClientConfigModel,
    KrakenRESTAPICollectorConfigModel,
)
from kraken_modules.utils.enums import KrakenExitCodeEnum
from kraken_modules.utils.logging import KrakenStdandardLogger
from kraken_modules.utils.exceptions import KrakenScriptSuccess
from kraken_modules.utils import get_exitcode_from_exception

# libraries
from argparse import Namespace
import asyncio
import argparse
import json
import sys


if __name__ == "__main__":
    """
    kraken REST API => 활성 거래쌍 정보를 가져와서 동기화하는 코드의 엔트리 포인트
    """
    logger: KrakenStdandardLogger = KrakenStdandardLogger(logger_name="MAIN")

    # 1. 필요 arguments 파싱
    try:
        logger.info_start(
            "argument 파싱",
        )
        parser = argparse.ArgumentParser(
            description="크라켄 거래쌍 결정 옵션 argument용 parser"
        )

        parser.add_argument(
            "--api_url", type=str, required=True, help="Kraken 거래쌍 API URL"
        )
        parser.add_argument(
            "--api_params",
            type=str,
            required=False,
            default="{}",
            help="Kraken 거래쌍 API params",
        )
        parser.add_argument(
            "--api_headers",
            type=str,
            required=False,
            default="{}",
            help="Kraken 거래쌍 API headers",
        )

        parser.add_argument(
            "--redis_url", type=str, required=True, help="GKE 내 Redis Service URL"
        )
        parser.add_argument(
            "--redis_key",
            type=str,
            required=True,
            help="크라켄 symbol 정보를 담는 레디스 키",
        )
        parser.add_argument(
            "--producer_urls",
            type=str,
            required=True,
            help="producer 쪽 url, 콤마로 구분된 string",
        )

        parser.add_argument(
            "--retry_num", type=int, required=False, default=5, help="retry 회수"
        )
        parser.add_argument(
            "--retry_delay",
            type=int,
            required=False,
            default=5,
            help="retry 딜레이 (초)",
        )
        parser.add_argument(
            "--conn_timeout",
            type=int,
            required=False,
            default=120,
            help="커넥션 타임아웃 (초)",
        )

        args: Namespace = parser.parse_args()
        logger.info_success(
            description="argument 파싱",
        )
    except Exception as e:
        logger.exception_common(
            error=e,
            description="argument 파싱",
        )
        sys.exit(KrakenExitCodeEnum.INVALID_ARGS_ERR.value)

    # 2. arguments 전처리
    try:
        logger.info_start("argument 전처리 - params, headers")
        args.api_params = json.loads(args.api_params)
        args.api_headers = json.loads(args.api_headers)
        logger.info_success("argument 전처리 - params, headers")
    except Exception as e:
        logger.exception_common(error=e, description=f"params or headers JSON loads")
        sys.exit(KrakenExitCodeEnum.JSON_LOAD_ERR.value)

    # 3. REDIS CLIENT 생성
    redis_client_config = KrakenRedisClientConfigModel(
        redis_url=args.redis_url,
        component_name="REDIS CLIENT",
        retry_num=args.retry_num,
        retry_delay=args.retry_delay,
        conn_timeout=args.conn_timeout,
    )
    redis_client = KrakenRedisClient(config=redis_client_config)
    asyncio.run(redis_client.initialize_redis())

    # 4. REST CLIENT 생성
    rest_client_config = KrakenRESTClientConfigModel(
        component_name="REST CLIENT",
        retry_num=args.retry_num,
        retry_delay=args.retry_delay,
        conn_timeout=args.conn_timeout,
    )
    rest_client = KrakenRESTClient(config=rest_client_config)

    # 5. Collector 생성
    collector_config = KrakenRESTAPICollectorConfigModel(
        component_name="REST API ACTIVE SYMBOL COLLECTOR",
        api_url=args.api_url,
        kraken_redis_key=args.redis_key,
        producer_urls=args.producer_urls,
        api_params=args.api_params,
        api_headers=args.api_headers,
        retry_num=args.retry_num,
        retry_delay=args.retry_delay,
        conn_timeout=args.conn_timeout,
    )
    collector = KrakenActiveSymbolsRestApiCollector(
        config=collector_config, redis_client=redis_client, rest_client=rest_client
    )

    try:
        logger.info_start("Kraken active 거래쌍 수집")
        asyncio.run(collector.run())
        logger.info_success("Kraken active 거래쌍 수집")
    except Exception as e:
        logger.exception_common(error=e, description="Kraken active 거래쌍 수집")
        sys.exit(get_exitcode_from_exception(e))

    sys.exit(get_exitcode_from_exception(KrakenScriptSuccess))
