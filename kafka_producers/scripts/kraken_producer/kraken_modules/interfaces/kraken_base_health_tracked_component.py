from abc import ABC, abstractmethod
from typing import Tuple
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerComponentHealthStatus
from kraken_modules.managers.kraken_producer_status_manager import KrakenProducerStatusManager

# TODO: update_component_status 객체 구현 내용을 각 객체에게 맡기지 말고 여기로 모으기
class KrakenBaseHealthTrackedComponent(ABC):
    def __init__(self, status_manager: KrakenProducerStatusManager):
        self.component_name: str 
        self.status_manager = status_manager

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
        await self.status_manager.update_manager_status(component_name=self.component_name, new_status=self.check_component_health())
