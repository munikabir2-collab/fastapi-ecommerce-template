from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from models import User

from database import SessionLocal
import models
from dependencies import get_current_user

router = APIRouter(
    prefix="/shop",
    tags=["Shop"]
)

#templates = Jinja2Templates(directory="templates")

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
# ADD SHOP (STATIC ROUTES FIRST)
# ---------------------------

@router.get("/add")
def shop_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        "shop_form.html",
        {"request": request}
    )

@router.post("/add")
def save_shop_detail(
    shop_name: str = Form(...),
    shop_location: str = Form(...),
    shop_description: str = Form(None),
    db: Session = Depends(fast_db),
    current_user: models.User = Depends(get_current_user)
):
    current_user.shop_name = shop_name
    current_user.shop_location = shop_location
    current_user.shop_description = shop_description

    db.commit()
    db.refresh(current_user)

    return RedirectResponse(
        url=f"/shop/{current_user.id}",
        status_code=303
    )

# ---------------------------
# SHOP VIEW (DYNAMIC ROUTE LAST)
# ---------------------------

@router.get("/{seller_id}")
def shop_products(
    seller_id: int,
    request: Request,
    db: Session = Depends(fast_db)
):
    seller = (
        db.query(models.User)
        .filter(models.User.id == seller_id)
        .first()
    )

    if not seller:
        raise HTTPException(status_code=404, detail="Shop not found")

    return request.app.state.templates.TemplateResponse(
        "shop_view.html",
        {
            "request": request,
            "seller": seller
        }
    )
@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(fast_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    request.session["user_id"] = user.id   # ✅ MUST
    request.session["role"] = "user"       # optional but good

    return RedirectResponse("/shop/add", status_code=303)

