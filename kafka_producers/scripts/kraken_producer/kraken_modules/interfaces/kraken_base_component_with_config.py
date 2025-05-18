from abc import abstractmethod, ABC
from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel

class KrakenBaseComponentWithConfig(ABC):
    @abstractmethod
    def config_from_self(cls, config: KrakenBaseConfigModel):
        """자기 자신의 config 정보를 뱉어내는 메소드 구현"""
        raise NotImplementedError
