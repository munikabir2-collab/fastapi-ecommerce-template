import razorpay
from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import os
import qrcode
import uuid

router = APIRouter(prefix="/payment", tags=["Payment"])
templates = Jinja2Templates(directory="templates")


# ---------------------------
# DB
# ---------------------------
def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# Razorpay Client
# ---------------------------
def get_client():
    return razorpay.Client(
        auth=(os.getenv("RAZORPAY_KEY"), os.getenv("RAZORPAY_SECRET"))
    )


# ---------------------------
# PAYMENT PAGE
# ---------------------------
@router.get("/{order_id}")
def payment_page(order_id: int, request: Request, db: Session = Depends(fast_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        return {"error": "Order not found"}

    client = get_client()

    razorpay_order = client.order.create({
        "amount": int(float(order.total) * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    order.razorpay_order_id = razorpay_order["id"]
    db.commit()

    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "order": order,
            "razorpay_key": os.getenv("RAZORPAY_KEY"),
            "razorpay_order_id": razorpay_order["id"]
        }
    )


# ---------------------------
# UPI QR CODE
# ---------------------------
@router.get("/generate-qr/{order_id}")
def generate_qr(order_id: int, db: Session = Depends(fast_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        return {"error": "Order not found"}

    upi_id = "7061691018@ybl"  # 🔴 replace this

    upi_link = f"upi://pay?pa={upi_id}&pn=MyShop&am={order.total}&cu=INR"

    file_path = f"upi_qr_{uuid.uuid4().hex}.png"

    img = qrcode.make(upi_link)
    img.save(file_path)

    return FileResponse(file_path)


# ---------------------------
# VERIFY PAYMENT
# ---------------------------
@router.post("/verify")
def verify_payment(
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    db: Session = Depends(fast_db)
):

    client = get_client()

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
    except Exception as e:
        print("Verification Failed:", e)
        return {"error": "Payment verification failed"}

    order = db.query(models.Order).filter(
        models.Order.razorpay_order_id == razorpay_order_id
    ).first()

    if not order:
        return {"error": "Order not found"}

    order.payment_status = "PAID"
    order.razorpay_payment_id = razorpay_payment_id

    db.commit()

    return RedirectResponse(f"/payment/success/{order.id}", status_code=303)


# ---------------------------
# SUCCESS PAGE
# ---------------------------
@router.get("/success/{order_id}")
def success(order_id: int, db: Session = Depends(fast_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if order:
        order.status = "CONFIRMED"
        db.commit()

    return RedirectResponse("/cart/success", status_code=303)