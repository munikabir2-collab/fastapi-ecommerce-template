from fastapi import APIRouter, Request, Depends, HTTPException, Form
from templates import templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import fast_db
from models import (
    User,
    Product,
    Order,
    OrderItem,
    Notification,
    SellerProfile,
    Subscription
)

router = APIRouter(
    prefix="/seller",
    tags=["Seller"]
)

#templates = Jinja2Templates(directory="templates")


# 🔐 Only seller access
def get_current_seller(request: Request):
    role = request.session.get("role")
    seller_id = request.session.get("user_id")   # FIXED

    if role != "seller":
        raise HTTPException(status_code=403, detail="Seller only")

    if not seller_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    return seller_id


# 🏪 Seller Dashboard / Profile
@router.get("/profile")
def seller_profile(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    print("CURRENT SELLER:", seller_id)
     
    seller = db.query(User).filter(User.id == seller_id).first()

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    # 🔥 Auto create profile
    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    if not profile:
        profile = SellerProfile(
            seller_id=seller_id,
            shop_name="My Shop",
            shop_description=""
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # 📦 Products
    products = db.query(Product).filter(
        Product.seller_id == seller_id
    ).order_by(Product.id.desc()).all()

    # 🔔 Notifications
    notifications = db.query(Notification).filter(
        Notification.seller_id == seller_id
    ).order_by(Notification.created_at.desc()).limit(20).all()

    # 📊 Orders
    total_orders = db.query(
        func.count(func.distinct(Order.id))
    ).join(
        OrderItem, OrderItem.order_id == Order.id
    ).filter(
        OrderItem.seller_id == seller_id
    ).scalar() or 0

    # 💰 Revenue
    total_revenue = db.query(
        func.coalesce(func.sum(OrderItem.price * OrderItem.qty), 0)
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        OrderItem.seller_id == seller_id
    ).scalar()

    stats = {
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

    # ⭐ Subscription
    subscription = db.query(Subscription).filter(
        Subscription.seller_id == seller_id,
        Subscription.is_active == True
    ).first()

    return templates.TemplateResponse(
        "seller_profile.html",
        {
            "request": request,
            "seller": seller,
            "profile": profile,
            "products": products,
            "notifications": notifications,
            "subscription": subscription,
            "stats": stats
        }
    )


# ✏ Edit Profile Page
@router.get("/profile/edit")
def edit_seller_profile(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):
    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    if not profile:
        # 🔥 auto create (optional but recommended)
        profile = SellerProfile(seller_id=seller_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return templates.TemplateResponse(
        "seller_profile_edit.html",
        {
            "request": request,
            "profile": profile
        }
    )

# 💾 Update Profile
@router.post("/profile/edit")
def update_seller_profile(
    shop_name: str = Form(...),
    shop_description: str = Form(None),

    # ✅ NEW FIELDS
    gst_no: str = Form(None),
    address: str = Form(None),
    state: str = Form(None),
    pincode: str = Form(None),

    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # ✅ SAVE ALL
    profile.shop_name = shop_name
    profile.shop_description = shop_description
    profile.gst_no = gst_no
    profile.address = address
    profile.state = state
    profile.pincode = pincode

    db.commit()

    return RedirectResponse("/seller/profile", status_code=303)
# 📦 Update Stock
@router.post("/product/{product_id}/stock")
def update_product_stock(
    product_id: int,
    stock: int = Form(...),
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock = stock
    db.commit()

    return RedirectResponse("/seller/profile", status_code=303)


# ⭐ Subscription Page
@router.get("/subscribe")
def seller_subscribe_page(
    request: Request,
    seller_id: int = Depends(get_current_seller)
):

    return templates.TemplateResponse(
        "seller_subscribe.html",
        {"request": request}
    )


# 💳 Subscribe
@router.post("/subscribe")
def seller_subscribe(
    request: Request,
    plan: str = Form(...),
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    expires = None

    if plan == "basic":
        expires = datetime.utcnow() + timedelta(days=30)

    elif plan == "pro":
        expires = datetime.utcnow() + timedelta(days=365)

    # deactivate old subscription
    db.query(Subscription).filter(
        Subscription.seller_id == seller_id
    ).update({"is_active": False})

    subscription = Subscription(
        seller_id=seller_id,
        plan=plan,
        is_active=True,
        expires_at=expires
    )

    db.add(subscription)
    db.commit()

    return RedirectResponse("/seller/profile", status_code=303)