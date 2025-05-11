from kraken_modules.kraken_rest_api_collector import KrakenActivePairsRestApiCollector
from kraken_modules.utils.enums.kraken_enums import KrakenExitCodeEnum
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger, get_error_msg
from kraken_modules.utils.map_exceptions_to_exit_code import get_exitcode_from_exception
from kraken_modules.utils.exceptions.kraken_success import KrakenScriptSuccess
import asyncio
import argparse
import json
import sys


if __name__ == "__main__":
    
    logger = get_stdout_logger(name="Kraken Active Pairs main logger")

    try: 
        logger.info("argument 파싱 시작!")
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

        args = parser.parse_args()
        logger.info("argument 파싱 완료!")
    except Exception as e:
        logger.exception(f"argument 파싱 중 에러로 종료!: {e}")
        sys.exit(KrakenExitCodeEnum.INVALID_ARGS_ERR.value)

    logger.info("argument 전처리 - params, headers 딕셔너리화 시작!")
    try:
        args.params = json.loads(args.params)
        args.headers = json.loads(args.headers)
    except TypeError as e:
        logger.exception(f"params 혹은 headers JSON loads 실패!: {e}")
        sys.exit(KrakenExitCodeEnum.JSON_LOAD_ERR.value)
    except Exception as e:
        logger.exception(f"params, headers 처리 중 알수없는 에러로 종료!: {e}")
        sys.exit(KrakenExitCodeEnum.UNKNOWN_ERR.value)
    logger.info("argument 전처리 - params, headers 딕셔너리화 완료!")

    logger.info("Kraken active 거래쌍 수집 시작!")
    try:
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
    except Exception as e:
        logger.exception(get_error_msg(e))
        sys.exit(get_exitcode_from_exception(e))
    logger.info("Kraken active 거래쌍 수집 완료!")

    sys.exit(get_exitcode_from_exception(KrakenScriptSuccess))
