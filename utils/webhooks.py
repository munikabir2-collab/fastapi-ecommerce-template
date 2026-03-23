import httpx

async def send_order_webhook(webhook_url: str, payload: dict):
    if not webhook_url:
        return

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            await client.post(webhook_url, json=payload)
        except Exception as e:
            print("Webhook failed:", e)