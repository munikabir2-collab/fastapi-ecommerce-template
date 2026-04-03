from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal
from models import User

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# -----------------------
# DB
# -----------------------
def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# PASSWORD
# -----------------------
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)


# -----------------------
# REGISTER
# -----------------------
@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    db: Session = Depends(fast_db)
):
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User already exists"}
        )

    user = User(
        username=username,
        name=name,
        email=email,
        phone=phone,
        address=address,
        state=state,
        pincode=pincode,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=303)


# -----------------------
# LOGIN
# -----------------------
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(fast_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    if user.role == "seller":
        return RedirectResponse("/seller/profile", status_code=303)

    return RedirectResponse("/products", status_code=303)


# -----------------------
# LOGOUT
# -----------------------
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)