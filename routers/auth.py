from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal
from models import User

router = APIRouter()

# Templates (IMPORTANT FIX)
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- REGISTER PAGE ----------------
@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None}
    )

# ---------------- REGISTER ----------------
@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == username).first()

    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User already exists"}
        )

    user = User(
        username=username,
        password=pwd_context.hash(password)
    )

    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=303)

# ---------------- LOGIN PAGE ----------------
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )

# ---------------- LOGIN ----------------
@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )

    # SESSION STORE
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    return RedirectResponse("/", status_code=303)

# ---------------- LOGOUT ----------------
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)