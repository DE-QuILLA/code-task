from kraken_modules.interfaces.kraken_base_component_with_config import KrakenBaseComponentWithConfig
from kraken_modules.interfaces.kraken_base_health_tracked_component import KrakenBaseHealthTrackedComponent
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from kraken_modules.utils.exceptions.kraken_custom_exceptions import KrakenProducerNotValidMessageTypeException
from aiokafka import AIOKafkaProducer
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import json

class KrakenKafkaClient(KrakenBaseComponentWithConfig, KrakenBaseHealthTrackedComponent):
    def __init__(self, bootstrap_server: str, status_manager: KrakenProducerStatusManager, health_topic_name: str, acks: Optional[str] = "1", retry_num: Optional[int] = 5, retry_delay: Optional[int] = 2, conn_timeout: Optional[int] = 20):
        self.bootstrap_server = bootstrap_server
        self.health_topic_name = health_topic_name or "__kafka_health_check"  # NOTE: 예시, 변경 가능
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.conn_timeout = conn_timeout
        self.retry_num = retry_num
        self.retry_delay = retry_delay
        self.acks = acks  # 현재 기본값 1(리더 브로커만 기다림), 향후 필요하면 상향 ("all" 등)

        self.component_name: str = "KAFKA CLIENT"
        self.producer: AIOKafkaProducer = None
        self.logger = KrakenStdandardLogger(
            logger_name=self.component_name,
        )

    async def initialize_kafka_client(self):
        try:
            self.logger.info_start("Kafka Client 초기화")
            await self.connect()

            await self.status_manager.register_component(component_name=self.component_name, new_component=self)
            self.logger.info_success("Kafka Client 초기화")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 초기화")
            raise e

    async def connect(self):
        await self._connect_with_retry()

    async def _connect_with_retry(self):
        try:
            self.logger.info_start("Kafka Client 연결")
            self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_server, acks=self.acks)
            await custom_retry(logger=self.logger, retry_num=self.retry_num, retry_delay=self.retry_delay, conn_timeout=self.conn_timeout, description="Kafka Client 연결", 
                        func=self.producer.start, func_kwargs=None)
            self.logger.info_success("Kafka Client 연결")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 연결")
            raise e

    async def close(self):
        self.logger.info_start(description="Kafka Client 종료")
        await self._close_with_retry()
        self.logger.info_success(description="Kafka Client 종료")
    
    async def _close_with_retry(self):
        try:
            self.logger.warning_common(description="Kafka Client 연결 종료 요청")
            await custom_retry(logger=self.logger, retry_num=self.retry_num, retry_delay=self.retry_delay, conn_timeout=self.conn_timeout, description="Kafka Client 연결 종료", 
                        func=self.producer.stop, func_kwargs=None)
            self.logger.info_success("Kafka Client 연결 종료")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 연결 종료")
            raise e

    async def produce(self, message: dict, topic_name: str):
        """메시지 발송 함수"""
        try:
            if isinstance(message, dict):
                msg = json.dumps(message,).encode("utf-8")
            elif isinstance(message, str):
                msg = message
            else:
                self.logger.warning_common("string 혹은 dict 타입이 아닌 메시지")
                raise KrakenProducerNotValidMessageTypeException(message=f"잘못된 타입의 메시지 [type: {type(message)}]")

            await custom_retry(logger=self.logger,
                         retry_num=self.retry_num,
                         retry_delay=self.retry_delay,
                         conn_timeout=self.conn_timeout,
                         description="Kafka 메시지 전송",
                         func=self.producer.send_and_wait,
                         func_kwargs={
                             "topic": topic_name,
                             "value": msg,
                         },)
        except Exception as e:
            self.logger.exception_common(f"Kafka 메시지 [{message}] 전송")
            raise e

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        헬스 체크용 메소드
        - 로직에 따라 자신의 건강 상태를 점검하고, 갱신할 KrakenProducerComponentHealthStatus 만들어서 반환함.
        - Client 등은 async 필요
        """
        try:
            test_msg = {"type": "health_check", "component": self.component_name}
            await self.produce(message=test_msg, topic_name=self.health_topic_name,)
            return KrakenProducerComponentHealthStatus(
                component_name=self.component_name,
                component=self,
                is_healthy=True,
                health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message="Kafka 헬스체크 메시지 전송 성공"
            )
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka 헬스 체크 실패")
            return KrakenProducerComponentHealthStatus(
                component_name=self.component_name,
                component=self,
                is_healthy=False,
                health_status_code=KrakenProducerStatusCodeEnum.ERROR.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message=str(e)
            )

    async def update_component_status(self) -> bool:
        """
        자신의 status를 업데이트하는 메소드
        - 필요 시 async 사용
        """
        new_status = await self.check_component_health()
        self.status_manager.update_manager_status(component_name=self.component_name, new_status=new_status)

