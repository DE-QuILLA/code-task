import logging
import sys
import traceback

def get_stdout_logger(logger_name: str) -> logging.Logger:
    """Airflow 웹 UI에서 확인하기 위해 stdout으로 출력하는 로거 생성"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_error_msg(error: Exception):
    return f"{type(error).__name__} 발생: {error}" + "\n" + f"{traceback.format_exc()}"
