from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import fast_db
from models import User, Order, Cart

router = APIRouter()
#templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user_id


@router.get("/user/profile")
def user_profile(
    request: Request,
    db: Session = Depends(fast_db),
    user_id: int = Depends(get_current_user)
):
    current_user = db.query(User).filter(User.id == user_id).first()

    user_orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.id.desc())
        .all()
    )

    cart_items = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .all()
    )

    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": current_user,
            "orders": user_orders,
            "cart_items": cart_items
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
