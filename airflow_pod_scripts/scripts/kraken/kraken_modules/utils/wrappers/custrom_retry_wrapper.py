from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from typing import Callable, Any, Coroutine, Optional, Dict
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
import async_timeout
import logging

async def custom_retry(
    logger: KrakenStdandardLogger,
    retry_num: int,
    retry_delay: int,
    conn_timeout: int,
    description: str,
    func: Callable[[], Coroutine[Any, Any, Any]],
    func_kwargs: Optional[Dict[str, Any]],
) -> Any:
    async with async_timeout.timeout(conn_timeout):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retry_num),
            wait=wait_fixed(retry_delay)
        ):
            with attempt:
                try:
                    logger.info_retry_start(attempt=attempt.retry_state.attempt_number, retry_num=retry_num, description=description,)
                    result = await func(**(func_kwargs or {}))
                    logger.info_retry_success(attempt=attempt.retry_state.attempt_number, retry_num=retry_num, description=description)
                    return result
                except Exception as e:
                    if attempt.retry_state.attempt_number >= retry_num:
                        logger.exception_retry_failure(attempt=attempt.retry_state.attempt_number, retry_num=retry_num, description=description, error=e)
                        raise e
                    else:
                        logger.warning_common(description=description)
