import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List
from kraken_modules.clients.kraken_websocket_client import KrakenWebSocketClient
from kraken_modules.config_models.kraken_websocket_client_configs import KrakenBaseWebSocketClientConfigModel
from kraken_modules.config_models.kraken_websocket_client_manager_config_model import KrakenWebSocketClientManagerConfigModel
from kraken_modules.logging.kraken_stdout_logger import KrakenStdandardLogger
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.managers.kraken_active_pair_manager import KrakenActivePairManager
from kraken_modules.clients.kraken_kafka_client import KrakenKafkaClient
from kraken_modules.interfaces.kraken_producer_base_component import KrakenBaseComponent
from kraken_modules.utils.enums.kraken_producer_status_code_enum import KrakenProducerStatusCodeEnum

class KrakenWebSocketClientManager(KrakenBaseComponent):
    def __init__(
        self,
        config: KrakenWebSocketClientManagerConfigModel,
        client_config_list: List[KrakenBaseWebSocketClientConfigModel],
        status_manager: KrakenProducerStatusManager,
        kafka_client: KrakenKafkaClient,
        active_pair_manager: KrakenActivePairManager,
    ):
        # config 기반 초기화
        self.component_name: str = config.component_name
        self.client_config_list = client_config_list

        # 동적 초기화 혹은 외부 객체 주입
        self.active_pair_manager = active_pair_manager
        self.status_manager = status_manager
        self.kafka_client = kafka_client
        self.logger: KrakenStdandardLogger = KrakenStdandardLogger(self.component_name)

        # 클라이언트 목록 {topic_name: client}
        self.clients: Dict[str, KrakenWebSocketClient] = {}

    async def init_clients_manager(self, config_list: List[KrakenBaseWebSocketClientConfigModel]):
        self.logger.info_start("웹소켓 클라이언트 매니저 초기화")
        await self.status_manager.register_component(component_name=self.component_name, new_component=self,)
        current_symbols, new_symbols,  = self.get_current_symbols()
        for config in config_list:
            self.logger.info_start(f"{config.channel} 웹소켓 클라이언트 생성")
            channel = config.channel
            config.symbol = current_symbols
            client = KrakenWebSocketClient(config=config, status_manager=self.status_manager, kafka_client=self.kafka_client)
            self.clients[channel] = client
            self.logger.info_success(f"{config.channel} 웹소켓 클라이언트 생성")
        self.logger.info_success("웹소켓 클라이언트 매니저 초기화")

    async def start_all(self):
        self.logger.info_start(f"{len(self.clients)} 개 WebSocket 클라이언트 동작")
        tasks = [client.run() for client in self.clients.values()]
        await asyncio.gather(*tasks)

    async def stop_all(self):
        self.logger.info_start(f"{len(self.clients)} 개 WebSocket 클라이언트 중단")
        tasks = [client.close() for client in self.clients.values()]
        await asyncio.gather(*tasks)

    def get_client(self, topic: str) -> KrakenWebSocketClient:
        return self.clients.get(topic)

    def get_all_topics(self) -> List[str]:
        return list(self.clients.keys())

    def get_current_symbols(self):
        return self.active_pair_manager.get_current_pairs()

    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        if len(self.clients) > 0:
            new_status = KrakenProducerComponentHealthStatus(
                component_name=self.component_name,
                component=self,
                is_healthy=len(self.clients) > 0,
                health_status_code=KrakenProducerStatusCodeEnum.STARTED.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message="웹소켓 클라이언트 매니저 정상",
            )
        else:
            new_status = KrakenProducerComponentHealthStatus(
                component_name=self.component_name,
                component=self,
                is_healthy=len(self.clients) > 0,
                health_status_code=KrakenProducerStatusCodeEnum.NO_OBJECT_TO_MANAGE.value,
                last_checked_at=datetime.now(ZoneInfo("Asia/Seoul")),
                message="웹소켓 클라이언트 매니저 정상",
            )
        return new_status

    async def update_component_status(self) -> bool:
        """
        자신의 status를 업데이트하는 메소드
        - 필요 시 async 사용
        """
        self.status_manager.update_manager_status(component_name=self.component_name, new_status=self.check_component_health())
    
    async def reload_symbols(self):
        new_total_symbols, new_subscription_symbols, new_unsubscription_symbols = await self.active_pair_manager.refresh()

        for client in self.clients.values():
            await client.update_symbols_and_subscriptions(
                new_total_symbols=new_total_symbols,
                new_sub_symobls=new_subscription_symbols,
                new_unsub_symbols=new_unsubscription_symbols,
            )
