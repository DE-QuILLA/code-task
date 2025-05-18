import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.config_models.kraken_websocket_client_configs import KrakenBaseWebSocketClientConfigModel
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.interfaces.kraken_base_component_with_config import KrakenBaseComponentWithConfig
from kraken_modules.interfaces.kraken_base_health_tracked_component import KrakenBaseHealthTrackedComponent
from kraken_modules.utils.wrapper.retry_wrapper_function import custom_retry
from typing import List, Optional


class KrakenWebSocketClient(KrakenBaseHealthTrackedComponent, KrakenBaseComponentWithConfig):
    def __init__(self, config: KrakenBaseWebSocketClientConfigModel, status_manager: KrakenProducerStatusManager, kafka_client: KrakenKafkaClient):
        self.config: KrakenBaseWebSocketClientConfigModel = config

        # 공통(고정) 속성 초기화
        self.url: str = config.url
        self.topic_name: str = config.topic_name
        self.retry_num: Optional[int] = config.retry_num or 5
        self.retry_delay: Optional[int] = config.retry_delay or 1
        self.conn_timeout: Optional[int] = config.conn_timeout or 20

        # 외부 객체
        self.kafka_client: KrakenKafkaClient =  kafka_client
        self.status_manager: KrakenProducerStatusManager = status_manager

        # 동적 초기화
        self.init_subscription_msg: str = config.subscription_msg
        self.component_name = f"{self.config.channel} CHANNEL - WEB SOCKET CLIENT"
        self.websocket: websockets.connect = None
        self.logger = KrakenStdandardLogger(f"{self.component_name}")

    async def initialize_websocket_client(self):
        await self.connect()
        await self.subscribe(subscription_message=self.init_subscription_msg)

    async def subscribe(self, sub_config: KrakenBaseWebSocketClientConfigModel):
        await self.send(sub_config.subscription_msg)

    async def unsubscribe(self, unsub_config: KrakenBaseWebSocketClientConfigModel):
        await self.send(unsub_config.unsubscription_msg)

    async def connect(self):
        self.logger.info_start("웹소켓 연결 시작")
        self.websocket = await self._connect_with_retry()
        self.logger.info_success("웹소켓 연결 성공")

    async def _connect_with_retry(self):
        return await custom_retry(logger=self.logger, retry_num=self.retry_num,
                           retry_delay=self.retry_delay, conn_timeout=self.conn_timeout, description=f"{self.config.channel} 웹소켓 연결",
                           func=websockets.connect, func_kwargs={"uri": self.url},)

    async def send(self, message: str):
        await self._send_with_retry(message=message)

    async def _send_with_retry(self, message: str):
        await custom_retry(
            logger=self.logger,
            retry_num=self.retry_num,
            retry_delay=self.retry_delay,
            conn_timeout=self.conn_timeout,
            description=f"[{self.config.channel}] 채널에 [{message}] 메시지 전송",
            func=self.websocket.send(message),
            
        )

    async def listen(self):
        try:
            self.logger.info_start("메시지 수신 루프 시작")
            async for message in self.websocket:
                # 여기서는 str로 옴 → Kafka에 그대로 넘김
                await self.kafka_client.produce(message=message, topic_name=self.topic_name)
        except Exception as e:
            raise e

    async def run(self,):
        while True:
            try:
                await self.initialize_websocket_client()
                await self.listen()
            except Exception as e:
                self.logger.exception_common(error=e, description=f"웹소켓 수신 중 오류, {self.retry_delay} 초 이후 재시도")
                await asyncio.sleep(self.retry_delay)

    async def close(self,):
        if self.websocket and not self.websocket.closed:
            await custom_retry(
                logger=self.logger,
                retry_num=self.retry_num,
                retry_delay=self.retry_delay,
                conn_timeout=self.conn_timeout,
                description="웹소켓 종료",
                func=self.websocket.close,
                func_kwargs={},
            )