import logging
import sys
import traceback
from typing import Type


def get_stdout_logger(logger_name: str) -> logging.Logger:
    """Fluent Bit 로그 수집을 고려, stdout, stderr로 출력하는 로거 생성"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        # 일반 로그 → stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)

        # 에러 로그 → stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)

        # 예시 포맷: [2025-05-13 01:20:00] [INFO] [REDIS CLIENT] Redis 연결 성공!
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

        stdout_handler.setFormatter(formatter)
        stderr_handler.setFormatter(formatter)

        logger.addHandler(stdout_handler)
        logger.addHandler(stderr_handler)

    return logger

def get_start_info_msg(description: str,) -> str:
    """일반적 info 레벨 로그 시작 형식 통일용 함수"""
    return f"{description} 시도 중!"

def get_success_info_msg(description: str,) -> str:
    """일반적 info 레벨 로그 완료 형식 통일용 함수"""
    return f"{description} 성공!"

def get_warning_msg(description: str,) -> str:
    """일반적 warning 레벨 로그 완료 형식 통일용 함수"""
    return f"{description} 발생!"

def get_exception_msg(error: Exception, description: str,) -> str:
    """일반적 exception 레벨 로그 형식 통일용 함수"""
    return f"{description} 중 {type(error).__name__} 발생: {error}" + "\n"  # logging.Logger.exception() 메소드는 traceback을 알아서 출력

def get_error_msg(error: Exception, description: str,) -> str:
    """일반적 error 레벨 로그 형식 통일용 함수"""
    return f"{description} 중 {type(error).__name__} 발생: {error}" + "\n" + f"{traceback.format_exc()}"

def get_repeated_start_info_msg(current_attempt_count: int, retry_num: int, description: str) -> str:
    """반복시도 info 레벨 로그 시작 형식 통일용 함수"""
    return f"{description} 중 {current_attempt_count}/{retry_num} 번째 시도 중!"

def get_repeated_success_info_msg(current_attempt_count: int, retry_num: int, description: str,) -> str:
    """반복시도 info 레벨 로그 완료 형식 통일용 함수"""
    return f"{description} 중 {current_attempt_count}/{retry_num} 번재 시도 성공!"

def get_repeated_failure_msg(description: str, current_attempt_count: int, retry_num: int, error_object: Exception,) -> None:
    """반복시도 warning, exception 레벨 실패 로그 형식 통일용 함수"""
    return f"{description} 중 {current_attempt_count}/{retry_num} 번째 시도 실패\n{type(error_object).__name__}: {error_object}\n"
