import uvicorn
import sys
from uvicorn.config import Config
from uvicorn.server import Server
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.config_models.kraken_standarad_logger_config_model import KrakenStandardLoggerConfigModel
from kafka_producers.scripts.kraken_producer.kraken_modules.utils.enums.map_exceptions_to_exit_code import get_exitcode_from_exception
from kraken_modules.utils.exceptions.kraken_custom_exceptions import KrakenProducerKafkaClientException


if __name__ == "__main__":
    """kraken_producer_main.py의 kraken_fast_api_app객체 실행"""
    uvicorn_level_logger_config = KrakenStandardLoggerConfigModel(logger_name="UVICORN",)
    uvicorn_level_logger = KrakenStdandardLogger(config=uvicorn_level_logger_config)

    uvicorn_level_logger.info_start(description="Uvicorn위 fast api 앱 실행")
    config = Config("kraken_producer_main:kraken_fast_api_app", host="0.0.0.0", port=8000)
    server = Server(config)

    exit_code = 0
    try:
        shoud_exit = server.run()
        if not shoud_exit:
            uvicorn_level_logger.warning_common(description="서버 비명시적 종료")
    except Exception as e:
        uvicorn_level_logger.exception_common(error=e, description="서버 실행 중 에러 발생",)
        sys.exit(get_exitcode_from_exception(e))
