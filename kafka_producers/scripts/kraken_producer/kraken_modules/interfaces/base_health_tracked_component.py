from abc import ABC, abstractmethod
from typing import Optional

class BaseHealthTrackedComponent(ABC):
    component_name: str

    def __init__(self, status_manager):
        self.status_manager = status_manager

    @abstractmethod
    async def check_health(self) -> bool:
        """
        헬스 체크용 메소드
        - 내부 로직 성공 여부 반환
        - 실패 시 False 반환
        """
        pass

    async def update_own_status(self):
        try:
            result = await self.check_health()
            self.status_manager.update_status(self.component_name, True, 0)
        except Exception as e:
            self.status_manager.update_status(self.component_name, False, 999, message=str(e))
