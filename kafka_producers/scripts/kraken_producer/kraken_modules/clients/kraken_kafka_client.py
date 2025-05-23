# custom
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.config_models import KrakenKafkaClientConfigModel
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.managers import KrakenProducerStatusManager
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.utils.wrapper import custom_retry
from kraken_modules.utils.exceptions import (
    KrakenProducerNotValidMessageTypeException,
    KrakenProducerKafkaClientConnectionException,
    KrakenProducerKafkaClientCloseFailureException,
    KrakenProducerProduceFailureException,
)

# libraries
from aiokafka import AIOKafkaProducer
from aiokafka.producer.message_accumulator import RecordMetadata
from datetime import datetime
from zoneinfo import ZoneInfo


class KrakenKafkaClient(KrakenBaseComponent):
    """
    카프카 클러스터와 연결을 표현하는 컴포넌트
    """

    def __init__(
        self,
        config: KrakenKafkaClientConfigModel,
        status_manager: KrakenProducerStatusManager,
    ):
        # config 객체 저장
        self.config: KrakenKafkaClientConfigModel = config

        # 외부 객체 혹은 동적 초기화
        self.status_manager: KrakenProducerStatusManager = status_manager
        self.producer: AIOKafkaProducer = None
        self.logger = KrakenStdandardLogger(
            logger_name=self.config.component_name,
        )

    async def initialize_kafka_client(self):
        """
        카프카 클라이언트 초기화
        - connect 수행
        - 스테이터스 매니저에 등록 수행
        """
        try:
            self.logger.info_start("Kafka Client 초기화")
            await self.connect()
            await self.status_manager.register_component(
                component_name=self.config.component_name, new_component=self
            )
            self.logger.info_success("Kafka Client 초기화")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 초기화")
            # NOTE: 내부 로직 그대로 raise
            raise

    async def connect(self):
        """
        retry 기반으로 카프카와 연결 수행
        """
        try:
            await self._connect_with_retry()
        except Exception as _:
            raise

    async def _connect_with_retry(self):
        """
        실제 카프카 연결 로직
        """
        try:
            self.logger.info_start("Kafka Client 연결")
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.config.bootstrap_server, acks=self.config.acks
            )
            await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description="Kafka Client 연결",
                func=self.producer.start,
            )
            self.logger.info_success("Kafka Client 연결")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 연결")
            raise KrakenProducerKafkaClientConnectionException(
                "Kafka 클라이언트 연결 실패"
            )

    async def close(self):
        """
        retry 기반으로 카프카와의 연결 종료 수행
        """
        try:
            self.logger.info_start(description="Kafka Client 종료")
            await self._close_with_retry()
            self.logger.info_success(description="Kafka Client 종료")
        except Exception as e:
            raise

    async def _close_with_retry(self):
        """
        실제 연결 종료 로직
        """
        try:
            self.logger.warning_common(description="Kafka Client 연결 종료 요청")
            await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description="Kafka Client 연결 종료",
                func=self.producer.stop,
            )
            self.logger.info_success("Kafka Client 연결 종료")
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka Client 연결 종료")
            raise KrakenProducerKafkaClientCloseFailureException(
                "Kafka Client 종료 실패"
            )

    async def produce(
        self,
        topic_name: str,
        message: str,
    ) -> RecordMetadata:
        """
        메시지 발송 함수
        - RecordMetadata: topic, partition, offset 등의 정보를 저장한 객체라고 함.
        """
        try:
            if not isinstance(message, str):
                self.logger.warning_common("string 타입이 아닌 메시지")
                raise KrakenProducerNotValidMessageTypeException(
                    message=f"잘못된 타입의 메시지 [type: {type(message)}]"
                )

            return await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description="Kafka 메시지 전송",
                func=self.producer.send_and_wait,
                func_kwargs={
                    "topic": topic_name,
                    "value": message,
                },
            )
        except Exception as e:
            self.logger.exception_common(f"Kafka 메시지 [{message}] 전송")
            raise KrakenProducerProduceFailureException(
                f"Kafka 메시지 전송 실패: {message}"
            )

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        헬스 체크용 KrakenProducerComponentHealthStatus 발행 메소드
        """
        try:
            test_msg = {"type": "health_check", "component": self.config.component_name}
            record_metadata: RecordMetadata = await self.produce(
                message=test_msg,
                topic_name=self.config.health_topic_name,
            )
            return KrakenProducerComponentHealthStatus(
                component_name=self.config.component_name,
                component=self,
                is_healthy=True,
                health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message=f"Kafka 헬스체크 메시지 전송 성공: \n[partition: {record_metadata.partition}] \n[offset: {record_metadata.offset}] \n[broker_received_at: {datetime.fromtimestamp(record_metadata.timestamp / 1000)}]",
            )
        except Exception as e:
            self.logger.exception_common(error=e, description="Kafka 헬스 체크 실패")
            return KrakenProducerComponentHealthStatus(
                component_name=self.config.component_name,
                component=self,
                is_healthy=False,
                health_status_code=KrakenProducerStatusCodeEnum.ERROR.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message=f"Kafka 헬스체크 메시지 전송 실패: {str(e)}",
            )
