from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
import json
import logging
from typing import Dict, Optional, Any


class DeqPodOperator(KubernetesPodOperator):
    """
    KubernetesPodOperator를 확장한 ETL 로직 관련 파이썬 스크립트 실행용 Pod 생성 오퍼레이터

    필수 파라미터
    :param script_path: Pod 내에서 실행할 엔트리포인트가 될 스크립트의 폴더 + 파일 경로(airflow_pod_scripts내의 경로) - ex) "kraken/some_script.py"

    선택 파라미터
    :param is_delete_operator_pod: 실행 후 해당 pod 삭제 여부 -> True면 삭제
    :param get_logs: 실행될 pod의 로그를 airflow에서 받아볼지 여부 -> True면 받아옴
    :param custom_args: 실행할 스크립트에 넘길 argv 딕셔너리
    :param cpu_request: Pod가 초기에 요청할 CPU 제한
    :param memory_request: Pod가 초기에 요청할 메모리 제한
    :param cpu_limit: Pod에 할당할 CPU 제한
    :param memory_limit: Pod에 할당할 메모리 제한
    :param image: 실행할 Docker 이미지 지정
    :param namespace: Pod가 실행될 K8S namespace
    """

    def __init__(
        self,
        script_path: str,
        is_delete_operator_pod: Optional[bool] = True,
        get_logs: Optional[bool] = True,
        custom_args: Optional[Dict[str, Any]] = None,
        cpu_request: Optional[str] = "500Mi",
        memory_request: Optional[str] = "512Mi",
        cpu_limit: Optional[str] = "1000m",
        memory_limit: Optional[str] = "1Gi",
        image: Optional[str] = "coffeeisnan/deq-airflow-pod-script:latest",
        namespace: Optional[str] = "airflow",
        *args,
        **kwargs,
    ):
        self.script_path = "/app/airflow_pod_scripts/" + script_path
        self.custom_args = custom_args or {}
        self.is_delete_operator_pod = is_delete_operator_pod
        self.get_logs = get_logs

        # 예시: kraken/main.py => [[DEQ-POD-OPERATOR] - [MAIN]]
        # NOTE: self.log는 super.__init__() 이후 접근 가능하기 때문에 Logger 클래스 사용
        script_file_name = self.script_path.split("/")[-1][:-3]
        self.logger: logging.Logger = logging.getLogger(
            f"[[DEQ-POD-OPERATOR] - [{script_file_name.upper()}]]"
        )

        # arguments 구성하기
        if self.custom_args:
            try:
                self.logger.info(f"arguments 구성 중!")
                arguments = self._generate_arguments()
                self.logger.info(f"arguement 구성 성공!: {arguments}")
            except Exception as e:
                self.logger.exception(f"argument 구성 실패!")
                raise e
        else:
            self.logger.info("argument 입력 없음!")

        # kwargs에서 arguments 제거
        if "arguments" in kwargs:
            self.logger.warning("kwargs 에서 arguments 필드 제거 중!")
            del kwargs["arguments"]
            self.logger.warning("kwargs 에서 arguments 필드 제거 성공!")
        else:
            self.logger.info("kwargs에서 arguments 필드 발견되지 않음!")

        # K8sPodOperator init 호출, 파이썬 스크립트 실행 명령어 제출
        super().__init__(
            cmds=["python", self.script_path],
            arguments=arguments,
            image=image,
            namespace=namespace,
            is_delete_operator_pod=self.is_delete_operator_pod,
            get_logs=self.get_logs,
            resources={
                "limit_cpu": cpu_limit,
                "limit_memory": memory_limit,
                "request_cpu": cpu_request,
                "request_memory": memory_request,
            }
            * args,
            **kwargs,
        )

    def _generate_arguments(self):
        """
        실행에 넘길 아규먼트를 병합하여 리스트로 반환
        """
        args = []

        for key, value in self.custom_args.items():
            args.append(f"--{key}")
            args.append(
                json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            )
        self.logger.info(f"구성된 arguments: {args}")

        return args
