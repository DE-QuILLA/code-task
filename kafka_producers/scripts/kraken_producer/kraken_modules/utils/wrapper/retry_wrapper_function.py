from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from typing import Callable, Any, Coroutine, Optional, Dict
from kraken_modules.utils.logging.kraken_stdout_logger import get_repeated_failure_msg, get_repeated_start_info_msg, get_repeated_success_info_msg
import async_timeout
import logging

async def custom_retry(
    logger: logging.Logger,
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
                    logger.info(get_repeated_start_info_msg(current_attempt_count=attempt.retry_state.attempt_number, retry_num=retry_num, description=description,))
                    result = await func(**(func_kwargs or {}))
                    logger.info(get_repeated_success_info_msg(current_attempt_count=attempt.retry_state.attempt_number, retry_num=retry_num, description=description,))
                    return result
                except Exception as e:
                    logger.warning(get_repeated_failure_msg(
                        description=description,
                        current_attempt_count=attempt.retry_state.attempt_number,
                        retry_num=retry_num,
                        error_object=e,
                    ))
                    if attempt.retry_state.attempt_number >= retry_num:
                        logger.exception(get_repeated_failure_msg(
                            description=description,
                            current_attempt_count=attempt.retry_state.attempt_number,
                            retry_num=retry_num,
                            error_object=e,
                        ))
                        raise e
