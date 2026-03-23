from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.ws_manager import manager

router = APIRouter()

@router.websocket("/ws/seller/{seller_id}")
async def seller_ws(websocket: WebSocket, seller_id: int):
    await manager.connect(seller_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(seller_id)
