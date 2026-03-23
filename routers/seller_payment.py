# routers/seller_payment.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from database import fast_db
from models import SellerBank, User, Order
import os
import razorpay

router = APIRouter(prefix="/seller/payment", tags=["Seller Payment"])

def get_current_seller(request: Request):
    seller_id = request.session.get("seller_id")
    if not seller_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    return seller_id

def get_client():
    key = os.getenv("RAZORPAY_KEY")
    secret = os.getenv("RAZORPAY_SECRET")
    return razorpay.Client(auth=(key, secret))


@router.post("/bank")
def add_bank(
    name: str = Form(...),
    account_number: str = Form(...),
    ifsc: str = Form(...),
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    client = get_client()

    # Razorpay beneficiary create
    beneficiary = client.partner.add_beneficiary({
        "name": name,
        "email": f"seller{seller_id}@example.com",
        "contact": "9999999999",
        "type": "bank_account",
        "bank_account": {
            "name": name,
            "ifsc": ifsc,
            "account_number": account_number
        }
    })

    # DB me save
    bank = db.query(SellerBank).filter(SellerBank.seller_id == seller_id).first()
    if not bank:
        bank = SellerBank(
            seller_id=seller_id,
            beneficiary_id=beneficiary["id"],
            name=name,
            account_number=account_number,
            ifsc=ifsc,
            bank_name=ifsc[:4]  # optional
        )
        db.add(bank)
    else:
        bank.name = name
        bank.account_number = account_number
        bank.ifsc = ifsc
        bank.beneficiary_id = beneficiary["id"]

    db.commit()
    return RedirectResponse("/seller/profile", status_code=302)


@router.post("/payout/{order_id}")
def payout_to_seller(
    order_id: int,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.seller_id == seller_id,
        Order.payment_status == "PAID"
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not paid")

    bank = db.query(SellerBank).filter(SellerBank.seller_id == seller_id).first()
    if not bank:
        raise HTTPException(status_code=400, detail="Bank account not linked")

    client = get_client()

    payout = client.payout.create({
        "account_number": os.getenv("RAZORPAY_ACCOUNT"),  # platform main account
        "fund_account_id": bank.beneficiary_id,
        "amount": int(order.total * 100),  # paise me
        "currency": "INR",
        "mode": "IMPS",
        "purpose": "payout",
        "queue_if_low_balance": True
    })

    # order me payout status update kar sakte ho
    order.seller_payout_status = "INITIATED"
    db.commit()

    return JSONResponse({"status": "success", "payout_id": payout["id"]})
