from airflow.models import BaseOperator
from airflow.utils.context import Context
import requests

class FastApiCommandOperator(BaseOperator):
    """
    Fast API로 구현된 ingestion producer에 정해진 명령어를 보내는 오퍼레이터

    필수 파라미터
    :param endpoint: 
    
    선택 파라미터
    :param is_delete_operator_pod: 실행 후 해당 pod 삭제 여부 -> True면 삭제
    :param get_logs: 실행될 pod의 로그를 airflow에서 받아볼지 여부 -> True면 받아옴
    :param custom_args: 실행할 스크립트에 넘길 argv 딕셔너리
    :param cpu_limit: Pod에 할당할 CPU 제한
    :param memory_limit: Pod에 할당할 메모리 제한
    :param image: 실행할 Docker 이미지 지정
    :param namespace: Pod가 실행될 K8S namespace
    """
    def __init__(
        self,
        endpoint: str,
        method: str = "POST",
        payload: dict = None,
        base_url: str = "http://kraken-producer.producer.svc.cluster.local:8000",
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

    def execute(self, context: Context):
        url = f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"
        self.log.info(f"[FastAPI 요청] {self.method.upper()} {url} payload={self.payload}")

        try:
            response = requests.request(
                method=self.method,
                url=url,
                json=self.payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            self.log.info(f"[FastAPI 응답] {response.status_code}: {response.text}")
        except requests.RequestException as e:
            self.log.error(f"❌ FastAPI 호출 실패: {e}")
            raise
