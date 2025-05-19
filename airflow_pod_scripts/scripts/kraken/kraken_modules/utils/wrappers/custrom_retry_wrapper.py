from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from typing import Callable, Any, Coroutine, Optional, Dict
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger
import async_timeout


async def custom_retry(
    logger: KrakenStdandardLogger,
    retry_num: int,
    retry_delay: int,
    conn_timeout: int,
    description: str,
    func: Callable[[], Coroutine[Any, Any, Any]],
    func_kwargs: Optional[Dict[str, Any]] = None,
    func_args: Optional[Tuple[Any]] = None,
) -> Any:
    async with async_timeout.timeout(conn_timeout):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retry_num),
            wait=wait_fixed(retry_delay)
        ):
            with attempt:
                try:
                    logger.info_retry_start(attempt=attempt.retry_state.attempt_number, retry_num=retry_num, retry_delay=retry_delay,)
                    func_args = func_args or ()
                    func_kwargs = func_kwargs or {}
                    result = await func(*func_args, **func_kwargs)
                    logger.info_retry_success(attempt=attempt.retry_state.attempt_number, retry_num=retry_num, retry_delay=retry_delay,)
                    return result
                except Exception as e:
                    logger.exception_retry_failure(
                        attempt=attempt.retry_state.attempt_number,
                        description=description,
                        retry_num=retry_num,
                        error=e
                    )
                    if attempt.retry_state.attempt_number >= retry_num:
                        raise
