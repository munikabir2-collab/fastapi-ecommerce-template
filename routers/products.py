from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from database import SessionLocal
import models

from starlette.status import HTTP_303_SEE_OTHER

# plan limit function
from utils.plan_limit import check_product_limit


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

templates = Jinja2Templates(directory="templates")


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
# Product List (Customer)
# ---------------------------
@router.get("/")
def product_list(
    request: Request,
    db: Session = Depends(fast_db)
):
    products = db.query(models.Product).all()

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products
        }
    )


# ---------------------------
# Add Product (Seller)
# ---------------------------
@router.post("/add")
def add_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(None),
    db: Session = Depends(fast_db)
):

    seller_id = request.session.get("user_id")

    # 🔹 Check plan limit
    check_product_limit(db, seller_id)

    product = models.Product(
        name=name,
        price=price,
        description=description,
        seller_id=seller_id
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return RedirectResponse("/seller/dashboard", status_code=HTTP_303_SEE_OTHER)