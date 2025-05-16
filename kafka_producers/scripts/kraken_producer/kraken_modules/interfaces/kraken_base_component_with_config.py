from abc import abstractmethod, ABC
from kraken_modules.config_models.kraken_base_config_model import KrakenBaseConfigModel

class KrakenBaseComponentWithConfig(ABC):
    @classmethod
    def from_config(cls, config: KrakenBaseConfigModel):
        """config객체로부터 자신을 만드는 메소드 구현"""
        return cls(**config.get_config_dict())
