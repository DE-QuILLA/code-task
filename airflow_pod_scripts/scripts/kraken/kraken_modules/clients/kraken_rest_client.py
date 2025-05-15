import aiohttp
from typing import Optional, Dict, Any
from kraken_modules.utils.wrappers.custrom_retry_wrapper import custom_retry
from kraken_modules.utils.logging.kraken_stdout_logger import KrakenStdandardLogger

class KrakenRestClient:
    def __init__(
        self,
        base_url: str,
        retry_num: int = 5,
        retry_delay: int = 1,
        timeout: int = 20,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = headers or {}
        self.logger = KrakenStdandardLogger(logger_name="KRAKEN REST CLIENT")

    async def fetch(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """GET 요청 후 JSON 응답 반환"""
        async with aiohttp.ClientSession() as session:
            return await custom_retry(
                logger=self.logger,
                retry_num=self.retry_num,
                retry_delay=self.retry_delay,
                conn_timeout=self.timeout,
                description=f"REST API 요청: {path}",
                func=self._get_json,
                func_kwargs={
                    "session": session,
                    "path": path,
                    "params": params,
                },
            )

    async def _get_json(self, session: aiohttp.ClientSession, path: str, params: Dict[str, Any] = None):
        url = f"{self.base_url}{path}"
        async with session.get(url, headers=self.headers, params=params) as response:
            response.raise_for_status()
            return await response.json()
