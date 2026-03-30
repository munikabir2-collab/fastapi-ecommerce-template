from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import fast_db
from models import Cart, Order, OrderItem
from utils.notifications import notify_seller
from utils.webhooks import send_order_webhook
import asyncio

router = APIRouter(prefix="/order", tags=["Order"])
#templates = Jinja2Templates(directory="templates")


# ---------------------------
# Helper: Get current logged-in user
# ---------------------------
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user_id


# ---------------------------
# Order Summary Page
# ---------------------------
@router.get("/")
def order_page(request: Request, db: Session = Depends(fast_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    total = sum(item.product.price * item.quantity for item in cart_items if item.product)

    return templates.TemplateResponse(
        "order.html",
        {"request": request, "cart_items": cart_items, "total": total}
    )


# ---------------------------
# Place Order
# ---------------------------
@router.post("/place-order")
async def place_order(request: Request, payment_method: str = Form(...), db: Session = Depends(fast_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")

    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = sum(item.product.price * item.quantity for item in cart_items if item.product)

    order = Order(
        user_id=user_id,
        total=total,
        status="PLACED",
        payment_method=payment_method,
        payment_status="PENDING"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Invoice number
    order.invoice_number = f"INV-{order.id}"
    db.add(order)
    db.commit()

    # Create order items
    seller_ids = set()
    for item in cart_items:
        product = item.product
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            seller_id=product.seller_id,
            qty=item.quantity,
            price=product.price,
            total_price=product.price * item.quantity
        )
        db.add(order_item)
        seller_ids.add(product.seller_id)
    db.commit()

    # Notify sellers
    for seller_id in seller_ids:
        await notify_seller(
            seller_id=seller_id,
            title="🛒 New Order",
            message=f"Order #{order.id} received"
        )

    # Send webhook
    asyncio.create_task(send_order_webhook(order.id))

    # Clear cart
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    db.commit()

    # Redirect payment
    if payment_method == "ONLINE":
        return RedirectResponse(f"/payment/{order.id}", status_code=303)
    return RedirectResponse("/cart/success", status_code=303)


# ---------------------------
# Order Details
# ---------------------------
@router.get("/details/{order_id}")
def order_details(order_id: int, request: Request, db: Session = Depends(fast_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    total = sum(item.total_price for item in order_items)

    return templates.TemplateResponse(
        "order_details.html",
        {"request": request, "order": order, "order_items": order_items, "total": total}
    )


# ---------------------------
# Cancel Order (User Profile)
# ---------------------------
@router.api_route("/cancel/{order_id}", methods=["GET", "POST"])
def cancel_order(order_id: int, db: Session = Depends(fast_db), user_id: int = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in ["SHIPPED", "DELIVERED"]:
        return {"error": "Order cannot be cancelled after shipping"}

    order.status = "CANCELLED"
    db.commit()
    return RedirectResponse("/user/profile", status_code=302)