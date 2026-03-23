from fastapi import WebSocket

class SellerConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, seller_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(seller_id, []).append(websocket)
        print("🟢 CONNECTED:", self.active_connections)

    def disconnect(self, seller_id: int, websocket: WebSocket):
        self.active_connections[seller_id].remove(websocket)
        print("🔴 DISCONNECTED:", self.active_connections)

    async def notify(self, seller_id: int, data: dict):
        print("📤 NOTIFY seller:", seller_id)
        print("📡 ACTIVE CONNECTIONS:", self.active_connections)

        for ws in self.active_connections.get(seller_id, []):
            await ws.send_json(data)

# ✅ SINGLE GLOBAL INSTANCE
manager = SellerConnectionManager()