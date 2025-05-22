# libraries
import aiohttp
from typing import Optional, Dict, Any

# custom
from kraken_modules.config_models import KrakenRESTClientConfigModel
from kraken_modules.utils.wrappers import custom_retry
from kraken_modules.utils.logging import KrakenStdandardLogger
from kraken_modules.utils.exceptions import KrakenRESTClientHTTPException


class KrakenRESTClient:
    def __init__(
        self,
        config: KrakenRESTClientConfigModel,
    ):
        # config 저장
        self.config = config

        # 외부 객체
        self.logger = KrakenStdandardLogger(logger_name=self.config.component_name)

    async def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        GET 요청 후 JSON 응답 그대로 반환(Retry 내장)
        """
        try:
            async with aiohttp.ClientSession() as session:
                return await custom_retry(
                    logger=self.logger,
                    retry_config=self.config.retry_config,
                    description=f"REST API 요청: {url}",
                    func=self._get_json,
                    func_kwargs={
                        "session": session,
                        "url": url,
                        "headers": headers,
                        "params": params,
                    },
                )
        except aiohttp.ClientResponseError as e:
            self.logger.exception_common(error=e, description=f"{url} 경로 api 호출 중 http 예외")
            raise KrakenRESTClientHTTPException(f"{url} API 호출 중 HTTP 관련 예외 발생")
        except Exception as e:
            self.logger.exception_common(error=e, description=f"{url} 경로 api 호출 중 일반 예외")
            raise 

    async def _get_json(self, session: aiohttp.ClientSession, url: str, headers: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        GET 요청 후 JSON 응답 반환하는 내부 로직
        """
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()
