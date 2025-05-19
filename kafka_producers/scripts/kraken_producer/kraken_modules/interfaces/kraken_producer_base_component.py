from abc import ABC, abstractmethod
from typing import Tuple
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager
from kraken_modules.config_models.kraken_websocket_client_configs import KrakenBaseWebSocketClientConfigModel
from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel


class KrakenBaseComponent(ABC):
    """Config 객체를 가지며, STATUS MANAGER에 등록되는 주요 컴포넌트 명세 인터페이스"""
    def __init__(self, status_manager: KrakenProducerStatusManager):
        self.config: KrakenBaseConfigModel
        self.status_manager = status_manager

    def config_from_self(self) -> KrakenBaseWebSocketClientConfigModel:
        """자기 자신의 config 정보를 뱉어내는 메소드 구현"""
        return self.config

    @abstractmethod
    async def check_component_health(self) -> KrakenProducerComponentHealthStatus:
        """
        헬스 체크용 메소드
        - 로직에 따라 자신의 건강 상태를 점검하고, 갱신할 KrakenProducerComponentHealthStatus 만들어서 반환함.
        - Client 등은 async 필요
        """
        raise NotImplementedError

    async def update_component_status(self) -> bool:
        """
        자신의 status를 업데이트하는 메소드
        - 필요 시 async 사용
        """
        await self.status_manager.update_manager_status(component_name=self.config.component_name, new_status=self.check_component_health())
