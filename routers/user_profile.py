from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from templates import templates
from database import fast_db
from models import User, Order, Cart

router = APIRouter()

# ---------------------------
# AUTH
# ---------------------------
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user_id

# ---------------------------
# SERIALIZERS
# ---------------------------
def serialize_user(user):
    if not user:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone
    }

def serialize_item(item):
    if not item:
        return None

    product_data = None
    if getattr(item, "product", None):
        product_data = {
            "name": getattr(item.product, "name", "N/A"),
            "price": float(getattr(item.product, "price", 0))
        }

    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "price": float(getattr(item, "price", 0)),
        "product": product_data
    }

# serializers.py
def serialize_order(order):
    return {
        "id": order.id,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "N/A",
        "status": order.status,
        "total_amount": float(order.total or 0),
        "order_items": [
            {
                "product_name": item.product_name or (item.product.name if item.product else "N/A"),
                "quantity": item.qty,
                "price": float(item.price),
                "total_price": float(item.total_price)
            }
            for item in getattr(order, "order_items", [])
        ]
    }
def serialize_cart(cart_item):
    if not cart_item:
        return None

    product_data = None
    if getattr(cart_item, 'product', None):
        product_data = {
            "name": getattr(cart_item.product, 'name', 'N/A'),
            "price": float(getattr(cart_item.product, 'price', 0))
        }

    return {
        "id": getattr(cart_item, 'id', 'N/A'),
        "product_id": getattr(cart_item, 'product_id', 'N/A'),
        "quantity": getattr(cart_item, 'quantity', 0),
        "product": product_data
    }

# ---------------------------
# ROUTES
# ---------------------------
@router.get("/user/profile")
def user_profile(
    request: Request,
    db: Session = Depends(fast_db),
    user_id: int = Depends(get_current_user)
):
    current_user = db.query(User).filter(User.id == user_id).first()
    user_orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.id.desc()).all()
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()

    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": serialize_user(current_user),
            "orders": [serialize_order(o) for o in user_orders],
            "cart_items": [serialize_cart(c) for c in cart_items]
        }
    )

@router.get("/user/profile/edit")
def edit_profile(
    request: Request,
    db: Session = Depends(fast_db),
    user_id: int = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()

    return templates.TemplateResponse(
        "user_profile_edit.html",
        {"request": request, "user": user}
    )

@router.post("/user/profile/edit")
def update_profile(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    db: Session = Depends(fast_db),
    user_id: int = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()

    user.name = name
    user.email = email
    user.phone = phone

    db.commit()
    return RedirectResponse("/user/profile", status_code=302)