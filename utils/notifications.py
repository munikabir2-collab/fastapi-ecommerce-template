from database import SessionLocal
from models import Notification
from datetime import datetime

async def notify_seller(seller_id: int, title: str, message: str):

    db = SessionLocal()

    notification = Notification(
        seller_id=seller_id,
        title=title,
        message=message,
        is_read=False,
        created_at=datetime.utcnow()
    )

    db.add(notification)
    db.commit()
    db.close()