from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, seller_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[seller_id] = websocket

    def disconnect(self, seller_id: int):
        self.active_connections.pop(seller_id, None)

    async def send_to_seller(self, seller_id: int, message: dict):
        websocket = self.active_connections.get(seller_id)
        if websocket:
            await websocket.send_json(message)

manager = ConnectionManager()