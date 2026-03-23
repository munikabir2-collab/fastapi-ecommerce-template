from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import SessionLocal
import models
from models import Cart, Product, Order, OrderItem
from routers.seller import send_notification

router = APIRouter(prefix="/cart", tags=["Cart"])
templates = Jinja2Templates(directory="templates")

# ---------------------------
# Auth
# ---------------------------
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")
    return user_id

# ---------------------------
# DB Dependency
# ---------------------------
def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Add to Cart
# ---------------------------
@router.post("/add/{product_id}")
def add_to_cart(
    product_id: int,
    request: Request,
    db: Session = Depends(fast_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart_item = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.product_id == product_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(
    user_id=user_id,
    product_id=product.id,
    quantity=1,
    price=product.price,          # ✅ store price
    product_name=product.name     # ✅ optional
)
        db.add(cart_item)

    db.commit()
    return RedirectResponse("/cart", status_code=303)

# ---------------------------
# View Cart
# ---------------------------
@router.get("/")
def view_cart(request: Request, db: Session = Depends(fast_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    items = db.query(Cart).filter(Cart.user_id == user_id).all()

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    return templates.TemplateResponse(
        "cart.html",
        {"request": request, "items": items, "total": total}
    )

# ---------------------------
# Remove Item
# ---------------------------
@router.post("/remove/{item_id}")
def remove_item(item_id: int, db: Session = Depends(fast_db)):
    item = db.query(Cart).filter(Cart.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/cart", status_code=303)

# ---------------------------
# Checkout
# ---------------------------
from fastapi import Form

@router.post("/checkout")
async def checkout(
    request: Request,
    payment_method: str = Form(...),   # ✅ IMPORTANT
    db: Session = Depends(fast_db),
    user_id: int = Depends(get_current_user)
):
    cart_items = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .all()
    )

    # 🚫 CART EMPTY
    if not cart_items:
        return templates.TemplateResponse(
            "cart_empty.html",
            {"request": request}
        )

    # ✅ SELLER
    seller_id = cart_items[0].product.seller_id

    # ✅ TOTAL (IMPORTANT FIX)
    total = sum(
        item.price * item.quantity
        for item in cart_items
    )

    # ✅ ORDER CREATE
    order = Order(
        user_id=user_id,
        seller_id=seller_id,
        total=total,
        status="PLACED",
        payment_method=payment_method,   # ✅ dynamic
        payment_status="PENDING"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # ✅ ORDER ITEMS
    for item in cart_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product.id,
            price=item.price,   # ✅ use stored price
            qty=item.quantity,
            seller_id=item.product.seller_id,
            total_price=item.price * item.quantity
        ))

    db.commit()

    # ❌ DO NOT DELETE CART YET (important for payment safety)

    # ---------------------------
    # 💳 ONLINE PAYMENT FLOW
    # ---------------------------
    if payment_method == "ONLINE":
        return RedirectResponse(
            f"/payment/{order.id}",
            status_code=303
        )

    # ---------------------------
    # 💰 COD FLOW
    # ---------------------------
    # clear cart only for COD
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    db.commit()

    return RedirectResponse("/cart/success", status_code=303)
# ---------------------------
# Success
# ---------------------------
@router.get("/success")
def order_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

    

@router.post("/increase/{item_id}")
def increase_qty(item_id: int, db: Session = Depends(fast_db)):
    item = db.query(Cart).filter(Cart.id == item_id).first()

    if item:
        item.quantity += 1
        db.commit()

    return RedirectResponse("/cart", status_code=303)
@router.post("/decrease/{item_id}")
def decrease_qty(item_id: int, db: Session = Depends(fast_db)):
    item = db.query(Cart).filter(Cart.id == item_id).first()

    if item:
        item.quantity -= 1

        if item.quantity <= 0:
            db.delete(item)
        db.commit()

    return RedirectResponse("/cart", status_code=303)    
