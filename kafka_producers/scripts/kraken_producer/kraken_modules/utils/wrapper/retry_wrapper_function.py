from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from typing import Callable, Any, Coroutine, Optional, Dict, Tuple
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.config_models.kraken_base_config_model import KrakenRetryConfig
import async_timeout

async def custom_retry(
    logger: KrakenStdandardLogger,
    retry_config: KrakenRetryConfig,
    description: str,
    func: Callable[[], Coroutine[Any, Any, Any]],
    func_kwargs: Optional[Dict[str, Any]] = None,
    func_args: Optional[Tuple[Any]] = None,
) -> Any:
    async with async_timeout.timeout(retry_config.conn_timeout):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retry_config.retry_num),
            wait=wait_fixed(retry_config.retry_delay)
        ):
            with attempt:
                try:
                    logger.info_retry_start(attempt=attempt.retry_state.attempt_number, retry_num=retry_config.retry_num, retry_delay=retry_config.retry_delay,)
                    func_args = func_args or ()
                    func_kwargs = func_kwargs or {}
                    result = await func(*func_args, **func_kwargs)
                    logger.info_retry_success(attempt=attempt.retry_state.attempt_number, retry_num=retry_config.retry_num, retry_delay=retry_config.retry_delay,)
                    return result
                except Exception as e:
                    logger.exception_retry_failure(
                        attempt=attempt.retry_state.attempt_number,
                        description=description,
                        retry_num=retry_config.retry_num,
                        error=e
                    )
                    if attempt.retry_state.attempt_number >= retry_config.retry_num:
                        raise
