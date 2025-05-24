import logging
import sys
import traceback


class StdandardLogger:
    """
    공통 로깅 포맷 및 핸들러 설정 제공 커스텀 로거 클래스
    """

    def __init__(self, logger_name: str, logging_level=logging.DEBUG):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging_level)

        if not self.logger.hasHandlers():
            # stdout => ERROR 미만 로깅
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.INFO)
            stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)

            # stderr => ERROR 로깅
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)

            # 공통 포매팅
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
            )

            stdout_handler.setFormatter(formatter)
            stderr_handler.setFormatter(formatter)

            self.logger.addHandler(stdout_handler)
            self.logger.addHandler(stderr_handler)

    def info_start(self, description: str) -> None:
        """INFO 레벨 시도 로그 메시지"""
        self.logger.info(f"{description} 시도 중!")

    def info_success(self, description: str) -> None:
        """INFO 레벨 성공 로그 메시지"""
        self.logger.info(f"{description} 성공!")

    def warning_common(self, description: str) -> None:
        """WARNING 레벨 이벤트 발생 로그 메시지"""
        self.logger.warning(f"{description} 발생!")

    def exception_common(self, error: Exception, description: str) -> None:
        """EXCEPTION 레벨 이벤트 발생 로그 메시지"""
        self.logger.exception(f"{description} 중 {type(error).__name__} 발생: {error}")

    def error_common(self, error: Exception, description: str) -> str:
        """ERROR 레벨 이벤트 발생 로그 메시지"""
        self.logger.error(
            f"{description} 중 {type(error).__name__} 발생: {error}\n{traceback.format_exc()}"
        )

    def info_retry_start(self, attempt: int, retry_num: int, description: str) -> str:
        """INFO 레벨 반복 작업 시도 로그 메시지"""
        self.logger.info(f"{description} 중 {attempt}/{retry_num} 번째 시도 중!")

    def info_retry_success(self, attempt: int, retry_num: int, description: str) -> str:
        """INFO 레벨 반복 작업 성공 로그 메시지"""
        self.logger.info(f"{description} 중 {attempt}/{retry_num} 번째 시도 성공!")

    def exception_retry_failure(
        self, attempt: int, retry_num: int, description: str, error: Exception
    ) -> str:
        """EXCEPTION 레벨 반복 작업 실패 로그 메시지"""
        self.logger.exception(
            f"{description} 중 {attempt}/{retry_num} 번째 시도 실패\n{type(error).__name__}: {error}\n"
        )
