from fastapi import APIRouter, Request, Form, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal
import models
from models import User, Notification
from fastapi.responses import FileResponse
from models import Order, OrderItem
from models import Product
import logging
from fastapi import UploadFile, File
import os, uuid, shutil
from utils.notifications import notify_seller

from models import SellerProfile
from utils.invoice import generate_invoice_pdf

# ---------------------------
# WebSocket Manager
# ---------------------------
class SellerSocketManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, seller_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[seller_id] = websocket

    def disconnect(self, seller_id: int):
        self.active_connections.pop(seller_id, None)

    async def send_notification(self, seller_id: int, data: dict):
        websocket = self.active_connections.get(seller_id)
        if websocket:
            await websocket.send_json(data)

manager = SellerSocketManager()

# ---------------------------
# Password hashing
# ---------------------------
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# ---------------------------
# Router & templates
# ---------------------------
router = APIRouter(prefix="/seller", tags=["seller"])

#templates = Jinja2Templates(directory="templates")

# ---------------------------
# DB dependency
# ---------------------------
def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Auth dependency
# ---------------------------
def get_current_seller(request: Request):
    seller_id = request.session.get("seller_id")
    if not seller_id:
        raise HTTPException(status_code=401, detail="Login required")
    return seller_id

# ---------------------------
# SELLER LOGIN / LOGOUT
# ---------------------------
@router.get("/login")
def seller_login_page(request: Request):
    return request.app.state.templates.TemplateResponse("seller_login.html", {"request": request})

@router.post("/login")
def seller_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(fast_db)):
    seller = db.query(User).filter(User.username == username).first()
    if not seller:
        raise HTTPException(status_code=401, detail="User not found")
    if not pwd_context.verify(password, seller.password):
        raise HTTPException(status_code=401, detail="Wrong password")

    request.session["seller_id"] = seller.id
    return RedirectResponse(url="/seller/dashboard", status_code=303)

@router.get("/logout")
def seller_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/seller/login", status_code=303)

# ---------------------------
# SELLER DASHBOARD
# ---------------------------

@router.get("/dashboard")
def seller_dashboard(request: Request, db: Session = Depends(fast_db), seller_id: int = Depends(get_current_seller)):
#    seller_id = request.session.get("seller_id")

    products = db.query(Product).filter(
        Product.seller_id == seller_id
    ).all()

    orders = db.query(Order).filter(
        Order.seller_id == seller_id
    ).order_by(Order.id.desc()).limit(5).all()

    notifications = db.query(Notification).filter(
        Notification.seller_id == seller_id
    ).order_by(Notification.id.desc()).limit(5).all()
      # ✅ 🔥 ADD THIS (BANK)
    bank = db.query(models.SellerBank).filter(
        models.SellerBank.seller_id == seller_id
    ).first()


    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "products": products,
            "orders": orders,
            "notifications": notifications,
            "seller": {"id": seller_id},
            "bank": bank
        }
    )
# ---------------------------
# ADD / SAVE PRODUCT
# ---------------------------
@router.get("/add_product")
def add_product_page(request: Request, seller_id: int = Depends(get_current_seller)):
    return request.app.state.templates.TemplateResponse("add_product.html", {"request": request})

@router.post("/add_product")
async def add_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    images: list[UploadFile] = File(None),   # ✅ ADD THIS
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    image_paths = []

    if images:
        os.makedirs("static/uploads", exist_ok=True)

        for img in images:
            filename = f"{uuid.uuid4()}_{img.filename}"
            file_path = f"static/uploads/{filename}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)

            image_paths.append("/" + file_path)

    product = models.Product(
        name=name,
        price=price,
        description=description,
        seller_id=seller_id,
        images=",".join(image_paths) if image_paths else None
    )

    db.add(product)
    db.commit()

    return RedirectResponse(url="/seller/dashboard", status_code=303)
# ---------------------------
# SELLER SALES PAGE
# ---------------------------
@router.get("/sales")
def seller_sales(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller),
):
    orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.seller_id == seller_id)
        .distinct()
        .all()
    )

    return templates.TemplateResponse(
        "sales.html",
        {
            "request": request,
            "orders": orders
        }
    )

# ---------------------------
# SELLER NOTIFICATIONS PAGE
# ---------------------------
@router.get("/notifications")
def seller_notifications(request: Request, db: Session = Depends(fast_db), seller_id: int = Depends(get_current_seller)):
    notifications = db.query(Notification).filter(Notification.seller_id == seller_id).order_by(Notification.created_at.desc()).limit(5).all()
    return templates.TemplateResponse("notifications.html", {"request": request, "notifications": notifications})

# ---------------------------
# DELETE PRODUCT
# ---------------------------
@router.post("/delete/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.seller_id == seller_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ✅ SOFT DELETE (yahi use karna hai)
    product.is_active = False
    db.commit()

    return RedirectResponse(url="/seller/dashboard", status_code=303)

# ---------------------------
# WEBSOCKET FOR REAL-TIME NOTIFICATIONS
# ---------------------------
@router.websocket("/ws/notifications")
async def seller_notification_ws(websocket: WebSocket):
    # Extract seller_id from query params (you can pass ?seller_id=44 if session unavailable)
    seller_id = websocket.query_params.get("seller_id")
    if not seller_id:
        await websocket.close()
        return
    seller_id = int(seller_id)

    await manager.connect(seller_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(seller_id)
# ---------------------------
# HELPER FUNCTION
# ---------------------------
async def send_notification(
    seller_id: int,
    title: str,
    message: str,
    db: Session
):
    notification = Notification(
        seller_id=seller_id,
        title=title,
        message=message
    )
    db.add(notification)
    db.commit()

    await manager.send_notification(
        seller_id,
        {
            "title": title,
            "message": message
        }
    )


@router.get("/order/{order_id}")
def seller_order_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = (
        db.query(Order)
        .join(OrderItem)
        .filter(
            Order.id == order_id,
            OrderItem.seller_id == seller_id   # ✅ IMPORTANT
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.seller_id == seller_id
        )
        .all()
    )

    return templates.TemplateResponse(
        "seller_order_detail.html",
        {
            "request": request,
            "order": order,
            "items": items
        }
    )

@router.get("/order/{order_id}/invoice")
def download_invoice(
    order_id: int,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.seller_id == seller_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order_id,
        OrderItem.seller_id == seller_id
    ).all()

    if not order_items:
        raise HTTPException(status_code=400, detail="No order items")

    # seller profile
    seller_profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    # ✅ CUSTOMER FETCH KARO
    customer = db.query(User).filter(
        User.id == order.user_id
    ).first()

    # ✅ INVOICE GENERATE
    pdf_path = generate_invoice_pdf(
        order,
        order_items,
        seller_profile,
        customer
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"GST_Invoice_{order.invoice_number}.pdf"
    )
@router.post("/order/{order_id}/accept")
async def accept_order(
    order_id: int,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.seller_id == seller_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "ACCEPTED"
    db.commit()

    # 🔔 Notification at SAME TIME
    await send_notification(
        seller_id=seller_id,
        title="Order Accepted",
        message=f"Order #{order_id} has been accepted",
        db=db
    )

    return RedirectResponse(
        url=f"/seller/order/{order_id}",
        status_code=303
    )

@router.post("/order/{order_id}/reject")
async def reject_order(
    order_id: int,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.seller_id == seller_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "REJECTED"
    db.commit()

    await send_notification(
        seller_id=seller_id,
        title="❌ Order Rejected",
        message=f"Order #{order_id} rejected",
        db=db
    )

    return RedirectResponse("/seller/dashboard", status_code=303)


@router.get("/order/{order_id}/invoice/view")
def view_invoice(
    order_id: int,
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.seller_id == seller_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order_id,
        OrderItem.seller_id == seller_id
    ).all()

    seller = db.query(User).filter(User.id == seller_id).first()
    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    grand_total = sum(item.price * item.qty for item in order_items)

    return templates.TemplateResponse(
        "invoice.html",
        {
            "request": request,
            "order": order,
            "order_items": order_items,
            "seller": seller,
            "profile": profile,
            "grand_total": grand_total
        }
    )


@router.get("/orders")
def seller_orders(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller),
):
    orders = (
        db.query(Order)
        .filter(Order.seller_id == seller_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "seller_orders.html",
        {
            "request": request,
            "orders": orders
        }
    )
@router.post("/assign_delivery/{order_id}/{delivery_boy_id}")
def assign_delivery(order_id: int, delivery_boy_id: int, db: Session = Depends(fast_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    delivery_boy = db.query(models.DeliveryBoy).filter(models.DeliveryBoy.id == delivery_boy_id).first()

    if not order or not delivery_boy:
        return {"error": "Order or Delivery Boy not found"}

    order.status = "SHIPPED"

    tracking = models.OrderTracking(
        order_id=order.id,
        status="SHIPPED",
        message=f"Order assigned to {delivery_boy.name}",
        updated_by="SELLER"
    )
    db.add(tracking)
    db.commit()

    return {"message": f"Order {order.id} assigned to {delivery_boy.name}"}

