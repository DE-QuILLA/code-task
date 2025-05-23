from kraken_modules.config_models import KrakenBaseConfigModel
import logging


class KrakenStandardLoggerConfigModel(KrakenBaseConfigModel):
    """Stdout, Stderr 용 로거 객체 초기화 인풋 명세 모델"""

    logger_name: str = __name__
    logging_level: int = logging.DEBUG
