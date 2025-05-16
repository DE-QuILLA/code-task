from airflow_pod_scripts.scripts.kraken.kraken_modules.collectors.kraken_rest_api_collector import KrakenActivePairsRestApiCollector
from kraken_modules.utils.enums.kraken_enums import KrakenExitCodeEnum
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.map_exceptions_to_exit_code import get_exitcode_from_exception
from kraken_modules.utils.exceptions.kraken_success import KrakenScriptSuccess
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

    try: 
        logger.info_start("argument 파싱",)
        parser = argparse.ArgumentParser(description="크라켄 거래쌍 결정 옵션 argument용 parser")

        parser.add_argument("--api_url", type=str, required=True, help="Kraken 거래쌍 API URL")
        parser.add_argument("--redis_url", type=str, required=True, help="GKE 내 Redis Service URL")
        parser.add_argument("--redis_key", type=str, required=True, help="Redis 내 저장할 키")
        parser.add_argument("--producer_url", type=str, required=True, help="상태를 갱신할 producer의 api로 연결된 url")
        parser.add_argument("--params", type=str, required=False, default='{}', help="Kraken 거래쌍 API params")
        parser.add_argument("--headers", type=str, required=False, default='{}', help="Kraken 거래쌍 API headers")
        parser.add_argument("--retry_num", type=int, required=False, default=5, help="retry 회수")
        parser.add_argument("--retry_delay", type=int, required=False, default=5, help="retry 딜레이 (초)")
        parser.add_argument("--timeout", type=int, required=False, default=120, help="커넥션 타임아웃 (초)")

        args: Namespace = parser.parse_args()
        logger.info_success(description="argument 파싱",)
    except Exception as e:
        logger.exception_common(error=e, description="argument 파싱",)
        sys.exit(KrakenExitCodeEnum.INVALID_ARGS_ERR.value)

    
    try:
        logger.info_start("argument 전처리 - params, headers")
        args.params = json.loads(args.params)
        args.headers = json.loads(args.headers)
        logger.info_success("argument 전처리 - params, headers")
    except Exception as e:
        logger.exception_common(error=e, description=f"params or headers JSON loads")
        sys.exit(KrakenExitCodeEnum.JSON_LOAD_ERR.value)

    try:
        logger.info_start("Kraken active 거래쌍 수집")
        collector = KrakenActivePairsRestApiCollector(
            api_url=args.api_url,
            redis_url=args.redis_url,
            redis_key=args.redis_key,
            producer_url=args.producer_url,
            params=args.params,
            headers=args.headers,
            retry_num=args.retry_num,
            retry_delay=args.retry_delay,
            timeout=args.timeout,
            )
        asyncio.run(collector.run())
        logger.info_success("Kraken active 거래쌍 수집")
    except Exception as e:
        logger.exception_common(error=e, description="Kraken active 거래쌍 수집")
        sys.exit(get_exitcode_from_exception(e))

    sys.exit(get_exitcode_from_exception(KrakenScriptSuccess))
