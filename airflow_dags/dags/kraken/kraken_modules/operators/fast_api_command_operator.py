from airflow.models import BaseOperator
from airflow.utils.context import Context
import requests

class FastApiCommandOperator(BaseOperator):
    """
    FastAPI에 명령을 전달하는 Airflow 커스텀 오퍼레이터
    - 지정된 REST API 엔드포인트로 HTTP 요청을 보내는 데에 사용됨

    필수 파라미터:
    :param endpoint: 호출할 FastAPI 앱 엔드포인트 경로 (예: /subscribe 또는 control/start)

    선택 파라미터:
    :param method: HTTP 메서드
    :param payload: 전송할 JSON 본문 데이터
    :param base_url: API 호출 대상 기본 주소
    :param headers: HTTP 요청 헤더
    :param timeout: 요청 타임아웃 시간(초)
    """
    def __init__(
        self,
        endpoint: str,
        method: str = "POST",
        payload: dict = None,
        base_url: str = "http://kraken-producer.producer.svc.cluster.local:8000",  # NOTE: 예시, 추후 수정될 수 있음.
        headers: dict = {"Content-Type": "application/json"},
        timeout: int = 10,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.endpoint = endpoint
        self.method = method
        self.payload = payload or {}
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self.log_msg_prefix = "[FAST API COMMAND OPERATOR]"

    def execute(self, context: Context):
        self.log.info(f"{self.log_msg_prefix} 동작 시작!")
        url = f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"

        try:
            self.log.info(f"{self.log_msg_prefix} 보낼 요청: \n{self.method.upper()} {url} payload={self.payload}")
            response = requests.request(
                method=self.method,
                url=url,
                json=self.payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            self.log.info(f"{self.log_msg_prefix} 응답: \n{response.status_code}: {response.text}")
        except Exception as e:
            self.log.exception(f"{self.log_msg_prefix} API 호출 중 에러 발생: \n")
            raise
