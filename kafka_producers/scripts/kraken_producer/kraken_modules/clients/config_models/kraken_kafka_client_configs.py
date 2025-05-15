from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Dict, Optional

class KrakenBaseKafkaClientConfigModel(BaseModel):
    bootstrap_server: str
    client_id: str

    @abstractmethod
    def som():
        pass
    
    @property
    def som():
        pass



