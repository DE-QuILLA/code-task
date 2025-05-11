from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
import json
import logging
from typing import Dict, Optional, Any


class DeqPodOperator(KubernetesPodOperator):
    """
    KubernetesPodOperator를 확장한 파이썬 스크립트 실행 Pod 생성 오퍼레이터

    필수 파라미터
    :param script_path: Pod 내에서 실행할 스크립트의 폴더 + 파일 경로(airflow_pod_scripts내의 경로) - ex) "kraken/some_script.py"
    
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
        script_path: str,
        is_delete_operator_pod: Optional[bool]=True,
        get_logs: Optional[bool]=True,
        custom_args: Optional[Dict[str, Any]]=None,
        cpu_limit: Optional[str]="1000m",
        memory_limit: Optional[str]="1Gi",
        image: Optional[str]="coffeeisnan/deq-airflow-pod-script:latest",
        namespace: Optional[str] ="airflow",
        *args,
        **kwargs,
    ):
        self.script_path = "/app/airflow_pod_scripts/" + script_path
        self.custom_args = custom_args or {}
        self.is_delete_operator_pod = is_delete_operator_pod
        self.logger = logging.getLogger(__name__)
        self.get_logs = get_logs

        # arguments 구성하기
        self.logger.info("1. arguments 구성 중")
        arguments = self._generate_arguments()

        # kwargs에서 arguments 제거
        if "arguments" in kwargs:
            self.log.warning("Removing duplicate 'arguments' from kwargs.")
            del kwargs["arguments"]

        # K8sPodOperator init 호출, 파이썬 스크립트 실행 가정
        super().__init__(
            cmds=["python", self.script_path],
            arguments=arguments,
            image=image,
            namespace=namespace,
            is_delete_operator_pod=self.is_delete_operator_pod,
            get_logs=self.get_logs,
            resources = {
                "limit_cpu": cpu_limit,
                "limit_memory": memory_limit,
                "request_cpu": cpu_limit,
                "request_memory": memory_limit,
            }
            *args,
            **kwargs,
        )

    def _generate_arguments(self):
        """실행에 넘길 아규먼트를 병합하여 리스트로 반환"""
        args = []

        for key, value in self.custom_args.items():
            args.append(f"--{key}")
            args.append(
                json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            )
        self.logger.info(f"구성된 arguments: {args}")

        return args
