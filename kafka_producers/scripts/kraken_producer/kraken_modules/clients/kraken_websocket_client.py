import websockets
import json
from datetime import datetime
from typing import Dict
from decimal import Decimal

# Decimal이 기본적으로 json - serializable 하지 않기 때문에 이친구가 필요함
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class KrakenWebSocketClient:
    def __init__(self, url: str, subscribe_dict: Dict):
        self.url = url
        self.subscribe_dict = subscribe_dict  # Dict
        self.subscribe_message = self._build_subscribe_message(subscribe_dict)  # str

    @staticmethod
    def _build_subscribe_message(subscribe_dict):
        return json.dumps(subscribe_dict)

    def _pretty_print_ticker(self, data):
        print(f"Time: [{datetime.now().isoformat()}]")
        print(f"Received Data: ")
        print(f"{json.dumps(data, indent=2, ensure_ascii=False, cls=DecimalEncoder)}")
        print("-" * 60)

    async def listen(self):
        async with websockets.connect(self.url) as ws:
            try:
                await ws.send(self.subscribe_message)
                print(f"Connected: Subscribed to {self.subscribe_dict.get('channel', 'Unknown channel')} for {', '.join(self.subscribe_dict.get('symbol', []))}")
            except Exception as e:
                print(f"Failed to connect: Connection failed")
                print(f"Error message: {e}")

            async for message in ws:
                msg = json.loads(message, parse_float=Decimal)
                self._pretty_print_ticker(msg)

