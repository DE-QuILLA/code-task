# custom
from kraken_modules.clients import KrakenWebSocketClient
from kraken_modules.config_models import KrakenBaseWebSocketClientConfigModel, KrakenWebSocketClientManagerConfigModel
from kraken_modules.data_models import KrakenProducerComponentHealthStatus
from kraken_modules.logging import KrakenStdandardLogger
from kraken_modules.managers import KrakenProducerStatusManager
from kraken_modules.managers import KrakenActiveSymbolManager
from kraken_modules.clients import KrakenKafkaClient
from kraken_modules.interfaces import KrakenBaseComponent
from kraken_modules.utils.enums import KrakenProducerStatusCodeEnum

# libraries
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List


class KrakenWebSocketClientManager(KrakenBaseComponent):
    def __init__(
        self,
        config: KrakenWebSocketClientManagerConfigModel,
        client_config_list: List[KrakenBaseWebSocketClientConfigModel],
        status_manager: KrakenProducerStatusManager,
        kafka_client: KrakenKafkaClient,
        active_pair_manager: KrakenActiveSymbolManager,
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

    async def initialize_clients_manager(self, config_list: List[KrakenBaseWebSocketClientConfigModel]):
        self.logger.info_start("웹소켓 클라이언트 매니저 초기화")
        await self.status_manager.register_component(component_name=self.component_name, new_component=self,)
        current_symbols = self.get_current_symbols()
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
        self.logger.info_success(f"{len(self.clients)} 개 WebSocket 클라이언트 동작")

    async def stop_all(self):
        self.logger.info_start(f"{len(self.clients)} 개 WebSocket 클라이언트 중단")
        tasks = [client.close() for client in self.clients.values()]
        await asyncio.gather(*tasks)
        self.logger.info_success(f"{len(self.clients)} 개 WebSocket 클라이언트 중단")

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
                message=f"{self.config.component_name} 관리할 클라이언트 없음",
            )
        return new_status

    async def update_component_status(self) -> bool:
        """
        자신의 status를 업데이트하는 메소드
        - 필요 시 async 사용
        """
        await self.status_manager.update_manager_status(component_name=self.component_name, new_status=self.check_component_health())
    
    async def reload_symbols(self):
        """
        /reload 엔드 포인트에 의한 갱신 발생 시 실행
        - 각 웹소켓 클라이언트에 접근하여 구독목록 갱신함
        """
        self.logger.info_start(f"active symbols reload 명령 수행")
        new_total_symbols, new_subscription_symbols, new_unsubscription_symbols = await self.active_pair_manager.refresh()
        self.logger.logger.info(f"새로운 심볼: {len(new_total_symbols)} 개\n새로운 구독 심볼: {len(new_subscription_symbols)} 개\n새로운 구독 취소 심볼: {len(new_unsubscription_symbols)} 개")

        try:
            for client in self.clients.values():
                self.logger.info_start(f"{client.config.component_name} 구독 심볼 갱신")
                await client.update_symbols_and_subscriptions(
                    new_total_symbols=new_total_symbols,
                    new_sub_symobls=new_subscription_symbols,
                    new_unsub_symbols=new_unsubscription_symbols,
                )
                self.logger.info_success(f"{client.config.component_name} 구독 심볼 갱신")
        except Exception as e:
            self.logger.exception_common(f"{client.config.component_name} 구독 심볼 갱신")
            # 내부 에러 그대로 raise
            raise
