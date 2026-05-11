from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import fast_db
from templates import templates

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


# =====================================================
# AUTH
# =====================================================

def get_current_seller(request: Request):

    seller_id = request.session.get("seller_id")

    if not seller_id:
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )

    return seller_id
# =====================================================
# SELLER PROFILE / DASHBOARD
# =====================================================

@router.get("/profile")
def seller_profile(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    seller = db.query(User).filter(
        User.id == seller_id
    ).first()

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    # =================================================
    # PROFILE
    # =================================================

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

    # =================================================
    # PRODUCTS
    # =================================================

    products = db.query(Product).filter(
        Product.seller_id == seller_id
    ).order_by(Product.id.desc()).all()

    # =================================================
    # ORDERS
    # =================================================

    orders = db.query(Order).join(
        OrderItem,
        OrderItem.order_id == Order.id
    ).filter(
        OrderItem.seller_id == seller_id
    ).order_by(Order.id.desc()).all()

    # =================================================
    # NOTIFICATIONS
    # =================================================

    notifications = db.query(Notification).filter(
        Notification.seller_id == seller_id
    ).order_by(Notification.created_at.desc()).limit(20).all()

    # =================================================
    # STATS
    # =================================================

    total_orders = db.query(
        func.count(func.distinct(Order.id))
    ).join(
        OrderItem,
        OrderItem.order_id == Order.id
    ).filter(
        OrderItem.seller_id == seller_id
    ).scalar() or 0

    total_revenue = db.query(
        func.coalesce(
            func.sum(OrderItem.price * OrderItem.qty),
            0
        )
    ).filter(
        OrderItem.seller_id == seller_id
    ).scalar()

    stats = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products": len(products)
    }

    # =================================================
    # SUBSCRIPTION
    # =================================================

    subscription = db.query(Subscription).filter(
        Subscription.seller_id == seller_id,
        Subscription.is_active.is_(True)
    ).first()

    return templates.TemplateResponse(
        "seller_profile.html",
        {
            "request": request,
            "seller": seller,
            "profile": profile,
            "products": products,
            "orders": orders,
            "notifications": notifications,
            "subscription": subscription,
            "stats": stats
        }
    )


# =====================================================
# EDIT PROFILE PAGE
# =====================================================

@router.get("/profile/edit")
def edit_profile(
    request: Request,
    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    return templates.TemplateResponse(
        "seller_profile_edit.html",
        {
            "request": request,
            "profile": profile
        }
    )


# =====================================================
# UPDATE PROFILE
# =====================================================

@router.post("/profile/edit")
def update_profile(
    shop_name: str = Form(...),
    shop_description: str = Form(""),
    gst_no: str = Form(""),
    address: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),

    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    profile = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.shop_name = shop_name
    profile.shop_description = shop_description
    profile.gst_no = gst_no
    profile.address = address
    profile.state = state
    profile.pincode = pincode

    db.commit()

    return RedirectResponse(
        "/seller/profile",
        status_code=303
    )


# =====================================================
# UPDATE STOCK
# =====================================================

@router.post("/product/{product_id}/stock")
def update_stock(
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

    return RedirectResponse(
        "/seller/profile",
        status_code=303
    )


# =====================================================
# DASHBOARD REDIRECT
# =====================================================

@router.get("/dashboard")
def seller_dashboard():

    return RedirectResponse(
        url="/seller/profile",
        status_code=303
    )


# =====================================================
# CREATE PROFILE PAGE
# =====================================================

@router.get("/profile/create")
def create_profile_page(
    request: Request,
    seller_id: int = Depends(get_current_seller)
):

    return templates.TemplateResponse(
        "seller_profile_create.html",
        {
            "request": request
        }
    )


# =====================================================
# CREATE PROFILE
# =====================================================

@router.post("/profile/create")
def create_profile(
    shop_name: str = Form(...),
    shop_description: str = Form(""),
    gst_no: str = Form(""),
    address: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),

    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    existing = db.query(SellerProfile).filter(
        SellerProfile.seller_id == seller_id
    ).first()

    if existing:
        return RedirectResponse(
            "/seller/profile",
            status_code=303
        )

    profile = SellerProfile(
        seller_id=seller_id,
        shop_name=shop_name,
        shop_description=shop_description,
        gst_no=gst_no,
        address=address,
        state=state,
        pincode=pincode
    )

    db.add(profile)
    db.commit()

    return RedirectResponse(
        "/seller/profile",
        status_code=303
    )


# =====================================================
# SUBSCRIPTION PAGE
# =====================================================

@router.get("/subscribe")
def subscribe_page(
    request: Request,
    seller_id: int = Depends(get_current_seller)
):

    return templates.TemplateResponse(
        "seller_subscribe.html",
        {
            "request": request
        }
    )


# =====================================================
# SUBSCRIBE
# =====================================================

@router.post("/subscribe")
def subscribe(
    plan: str = Form(...),

    db: Session = Depends(fast_db),
    seller_id: int = Depends(get_current_seller)
):

    expires_at = None

    if plan == "basic":
        expires_at = datetime.utcnow() + timedelta(days=30)

    elif plan == "pro":
        expires_at = datetime.utcnow() + timedelta(days=365)

    db.query(Subscription).filter(
        Subscription.seller_id == seller_id
    ).update(
        {
            "is_active": False
        }
    )

    new_subscription = Subscription(
        seller_id=seller_id,
        plan=plan,
        is_active=True,
        expires_at=expires_at
    )

    db.add(new_subscription)
    db.commit()

    return RedirectResponse(
        "/seller/profile",
        status_code=303
    )    