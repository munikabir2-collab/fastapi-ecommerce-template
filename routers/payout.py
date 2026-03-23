from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import fast_db
import razorpay
import os
import models
import time
from datetime import datetime, timedelta
import logging
import hmac
import hashlib
router = APIRouter(prefix="/seller/payment", tags=["Seller Payout"])

logger = logging.getLogger(__name__)


def get_client():
    return razorpay.Client(
        auth=(os.getenv("RAZORPAY_KEY"), os.getenv("RAZORPAY_SECRET"))
    )


@router.post("/payout/{seller_id}")
def send_payout(seller_id: int, request: Request, db: Session = Depends(fast_db)):

    # 🔐 Admin check
    if request.session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    # ---------------------------
    # Seller + Bank check
    # ---------------------------
    seller = db.query(models.User).filter(models.User.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    bank = db.query(models.SellerBank).filter(
        models.SellerBank.seller_id == seller_id
    ).first()

    if not bank:
        raise HTTPException(status_code=404, detail="Bank details not found")

    # ---------------------------
    # 🛑 Idempotency (time-based)
    # ---------------------------
    recent_time = datetime.utcnow() - timedelta(minutes=5)

    existing = db.query(models.Payout).filter(
        models.Payout.seller_id == seller_id,
        models.Payout.created_at >= recent_time,
        models.Payout.status.in_(["queued", "processing", "processed"])
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Recent payout already in progress or completed"
        )

    # ---------------------------
    # STEP 1: LOCK + CALCULATE
    # ---------------------------
    order_items = db.query(models.OrderItem)\
        .with_for_update(skip_locked=True)\
        .join(models.Order)\
        .filter(
            models.OrderItem.seller_id == seller_id,
            models.Order.payment_status == "PAID",
            models.OrderItem.is_paid_to_seller == False
        ).all()

    if not order_items:
        raise HTTPException(status_code=400, detail="No earnings available")

    total = sum(item.total_price for item in order_items)
    commission = round(total * 0.10, 2)
    payout_amount = round(total - commission, 2)

    if payout_amount <= 0:
        raise HTTPException(status_code=400, detail="No payable amount")

    reference_id = f"seller_{seller_id}_{int(time.time())}"

    # ---------------------------
    # STEP 2: TEMP MARK (lock)
    # ---------------------------
    for item in order_items:
        item.is_paid_to_seller = True

    db.flush()
    db.commit()   # 🔓 release lock early

    client = get_client()

    try:
        # ---------------------------
        # STEP 3: Razorpay payout
        # ---------------------------
        payout = client.payout.create({
            "account_number": os.getenv("RAZORPAY_ACCOUNT_NUMBER"),
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": bank.account_holder_name,
                    "ifsc": bank.ifsc,
                    "account_number": bank.account_number
                }
            },
            "amount": int(payout_amount * 100),
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "payout",
            "queue_if_low_balance": True,
            "reference_id": reference_id,
            "narration": "Seller payout"
        })

        if payout.get("status") not in ["queued", "processing", "processed"]:
            raise Exception("Payout failed")

        # ---------------------------
        # STEP 4: Save payout record
        # ---------------------------
        payout_entry = models.Payout(
            seller_id=seller_id,
            amount=payout_amount,
            commission=commission,
            razorpay_payout_id=payout.get("id"),
            status=payout.get("status"),
            created_at=datetime.utcnow()
        )

        db.add(payout_entry)
        db.commit()

    except Exception as e:
        db.rollback()

        # 🔥 rollback payment flag
        for item in order_items:
            item.is_paid_to_seller = False
        db.commit()

        logger.error(f"PAYOUT ERROR seller={seller_id}: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Payout failed. Rolled back safely."
        )

    return {
        "status": "success",
        "seller_id": seller_id,
        "total_earnings": total,
        "commission": commission,
        "payout_amount": payout_amount,
        "items_paid": len(order_items),
        "payout_id": payout.get("id")
    }


@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(fast_db)):

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    event = data.get("event")
    payout_entity = data.get("payload", {}).get("payout", {}).get("entity", {})
    payout_id = payout_entity.get("id")

    if not payout_id:
        return {"status": "ignored"}

    payout = db.query(models.Payout).filter(
        models.Payout.razorpay_payout_id == payout_id
    ).first()

    if not payout:
        return {"status": "not_found"}

    # ---------------------------
    # STATUS HANDLING
    # ---------------------------
    if event == "payout.processed":
        payout.status = "processed"

    elif event == "payout.failed":
        payout.status = "failed"

        # 🔥 ONLY THIS PAYOUT rollback
        items = db.query(models.OrderItem).filter(
            models.OrderItem.payout_id == payout.id
        ).all()

        for item in items:
            item.is_paid_to_seller = False
            item.payout_id = None

    elif event == "payout.reversed":
        payout.status = "reversed"

    db.commit()

    return {"status": "ok"}    