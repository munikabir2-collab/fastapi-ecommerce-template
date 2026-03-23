from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook/order")
async def receive_order_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = None

    print("🔔 Webhook hit hua")
    print("Data:", data)

    return {"status": "ok"}