import uvicorn
import sys
from uvicorn.config import Config
from uvicorn.server import Server
from kraken_modules.utils.logging.kraken_stdout_logger import get_stdout_logger, get_error_msg
from kafka_producers.scripts.kraken_producer.kraken_modules.utils.enums.map_exceptions_to_exit_code import get_exitcode_from_exception
from kraken_modules.utils.exceptions.kraken_custom_exceptions import KrakenProducerKafkaClientException


if __name__ == "__main__":
    """kraken_producer_main.py의 kraken_fast_api_app객체 실행"""
    uvicorn_level_logger = get_stdout_logger("UVICORN LEVEL LOGGER")

    uvicorn_level_logger.info("Uvicorn에 의한 fast api 앱 실행!")
    config = Config("kraken_producer_main:kraken_fast_api_app", host="0.0.0.0", port=8000)
    server = Server(config)

    exit_code = 0
    try:
        shoud_exit = server.run()
        if not shoud_exit:
            uvicorn_level_logger.warning("서버가 명시적으로 종료되지 않음!")
    except Exception as e:
        uvicorn_level_logger.exception(get_error_msg(e))
        sys.exit(get_exitcode_from_exception(e))
