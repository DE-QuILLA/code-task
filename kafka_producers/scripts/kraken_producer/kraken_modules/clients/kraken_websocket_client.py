# custom
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.clients import KrakenKafkaClient
from kraken_modules.config_models import KrakenBaseWebSocketClientConfigModel, KrakenPingWebSocketClientConfigModel
from kraken_modules.managers import KrakenProducerStatusManager
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.utils.wrapper import custom_retry
from kraken_modules.utils.exceptions import KrakenProducerWebSocketClientConnectionException, KrakenProducerWebSocketClientMessageSendFailureException, KrakenProducerWebSocketClientSubscriptionFailureException, KrakenProducerWebSocketClientUnsubscriptionFailureException

# libraries
from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
import websockets
import json
import re


class KrakenWebSocketClient(KrakenBaseComponent):
    def __init__(self, config: KrakenBaseWebSocketClientConfigModel, status_manager: KrakenProducerStatusManager, kafka_client: KrakenKafkaClient,):
        # config 객체 저장
        self.config: KrakenBaseWebSocketClientConfigModel = config

        # 외부 객체 주입
        self.kafka_client: KrakenKafkaClient =  kafka_client
        self.status_manager: KrakenProducerStatusManager = status_manager

        # 동적 초기화
        self.websocket: websockets.connect = None
        self.logger = KrakenStdandardLogger(f"{self.config.component_name}")
        self._last_heartbeat_at: datetime = None
        self.heartbeat_regex = re.compile(r'"channel"\s*:\s*"heartbeat"')

    async def initialize_websocket_client(self,):
        try:
            self.logger.info_start(f"{self.config.component_name} 초기화")
            await self.connect()
            await self.update_symbols_and_subscriptions()
            self.logger.info_success(f"{self.config.component_name} 초기화")
        except Exception as _:
            self.logger.exception_common(f"{self.config.component_name} 초기화")
            # NOTE: 내부 예외 그대로 raise
            raise

    async def update_symbols_and_subscriptions(self, new_total_symbols: Optional[List[str]]=None, new_sub_symbols: Optional[List[str]]=None, new_unsub_symbols: Optional[List[str]]=None):
        # 1. 갱신 - 초기화 시 사용도 고려, optional parameter 사용
        self.config.symbol = new_total_symbols or self.config.symbol
        self.config.last_subscribe_symbol = new_sub_symbols or self.config.last_subscribe_symbol
        self.config.last_unsubscribe_symbol = new_unsub_symbols or self.config.last_unsubscribe_symbol

        # 실제 구독 / 구독 취소
        if self.config.last_subscribe_symbol:
            await self.subscribe()
        if self.config.last_unsubscribe_symbol:
            await self.unsubscribe()

    async def subscribe(self,):
        try:
            await self.send(self.config.subscription_msg)
        except Exception as e:
            raise KrakenProducerWebSocketClientSubscriptionFailureException(f"{self.config.component_name} 구독 실패 \n구독 메시지: {self.config.subscription_msg}")

    async def unsubscribe(self,):
        try:
            await self.send(self.config.unsubscription_msg)
        except Exception as e:
            raise KrakenProducerWebSocketClientUnsubscriptionFailureException(f"{self.config.component_name} 구독 취소 실패 \n구독 취소 메시지: {self.config.unsubscription_msg}")

    async def connect(self):
        try:
            self.logger.info_start(f"{self.config.channel} - 웹소켓 연결")
            self.websocket = await self._connect_with_retry()
            self.logger.info_success(f"{self.config.channel} - 웹소켓 연결")
        except Exception as e:
            self.logger.exception_common(f"{self.config.channel} - 웹소켓 연결")
            raise KrakenProducerWebSocketClientConnectionException(f"{self.config.channel} 웹소켓 연결 실패")

    async def _connect_with_retry(self):
        return await custom_retry(logger=self.logger, retry_config=self.config.retry_config, description=f"{self.config.channel} 웹소켓 연결",
                           func=websockets.connect, func_args=(self.config.url,),)

    async def send(self, message: str):
        try:
            self.logger.info_start(f"{self.config.channel} 채널로 [{message}] 메시지 전송")
            await self._send_with_retry(message=message)
            self.logger.info_success(f"{self.config.channel} 채널로 [{message}] 메시지 전송")
        except Exception as e:
            self.logger.exception_common(f"{self.config.channel} 채널로 [{message}] 메시지 전송")
            error_msg = f"{self.config.channel} 채널로 메시지 전송 실패\n" + f"메시지: \n{json.dumps(message, indent=2, ensure_ascii=False)}"
            raise KrakenProducerWebSocketClientMessageSendFailureException(error_msg)

    async def _send_with_retry(self, message: str):
        await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"[{self.config.channel}] 채널에 [{message}] 메시지 전송",
            func=self.websocket.send,
            func_args=(message,)
        )

    async def listen(self):
        try:
            self.logger.info_start("메시지 수신 루프 시작")
            async for message in self.websocket:
                if self.heartbeat_regex.search(message):
                    self._last_heartbeat_at = datetime.now(ZoneInfo("Asia/Seoul"))
                await self.kafka_client.produce(message=message, topic_name=self.config.topic_name)  # str로 들어와서 바로 json - dumps 없이 넘김
        except Exception as e:
            # NOTE: 카프카 클라이언트의 예외이므로 그대로 raise
            raise

    async def run(self,):
        self.logger.info_start(f"{self.config.component_name} 실행")
        while True:
            try:
                await self.initialize_websocket_client()
                await self.listen()
            except Exception as e:
                self.logger.exception_common(error=e, description=f"웹소켓 수신 중 오류, {self.config.retry_config.retry_delay} 초 이후 재시도")
                await asyncio.sleep(self.config.retry_config.retry_delay)

    async def close(self,):
        self.logger.info_start(f"{self.config.component_name} 종료")
        if self.websocket and not self.websocket.closed:
            await custom_retry(
                logger=self.logger,
                retry_config=self.config.retry_config,
                description=f"{self.config.component_name} 종료",
                func=self.websocket.close,
            )
        self.logger.info_success(f"{self.config.component_name} 종료")
    
    async def ping(self):
        ping_msg: str = KrakenPingWebSocketClientConfigModel().subscription_msg
        await custom_retry(
            logger=self.logger,
            retry_config=self.config.retry_config,
            description=f"{self.config.component_name} PING 시도",
            func=self.send,
            func_kwargs={"message": ping_msg}
        )

    async def check_component_health(self):
        if self._last_heartbeat_at is None:
            return KrakenProducerComponentHealthStatus(
                component_name=self.config.component_name,
                component=self,
                is_healthy=True,
                health_status_code=KrakenProducerStatusCodeEnum.NOT_STARTED.value,
                message=f"아직 HeartBeat 수신 이력 없음",
            )

        now = datetime.now(ZoneInfo("Asia/Seoul"))
        time_diff: timedelta = now - self._last_heartbeat_at

        if time_diff < timedelta(seconds=3):
            return KrakenProducerComponentHealthStatus(
                component_name=self.config.component_name,
                component=self,
                is_healthy=True,
                health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                message=f"{time_diff.total_seconds():.2f} 초 이전 HeartBeat 응답 수신됨",
            )
        else:
            return KrakenProducerComponentHealthStatus(
                component_name=self.config.component_name,
                component=self,
                is_healthy=False,
                health_status_code=KrakenProducerStatusCodeEnum.NO_HEART_BEAT.value,
                message=f"{time_diff.total_seconds():.2f} 초 이전 HeartBeat 응답 수신됨",
            )

