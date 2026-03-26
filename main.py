# main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database import engine, Base
from auth import router as auth_router
import os
from fastapi.responses import HTMLResponse
from routers import (
    cart,
    products,
    seller,
    order,
    shop,
    payment,
    webhook,
    seller_profile,
    user_profile,
    subscription
)
load_dotenv(override=True)
# -----------------------
# APP SETUP
# -----------------------
app = FastAPI(debug=True)

app.add_middleware(
    SessionMiddleware,
    secret_key="supersecretkey"
)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

# -----------------------
# ROUTERS
# -----------------------
app.include_router(auth_router)   # 🔐 AUTH ROUTES

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(seller.router)
app.include_router(shop.router)
app.include_router(payment.router)
app.include_router(webhook.router)
app.include_router(seller_profile.router)
app.include_router(user_profile.router)
app.include_router(subscription.router)
app.include_router(payment.router, prefix="/seller")
# -----------------------
# STATIC
# -----------------------

# ✅ Absolute path (VERY IMPORTANT)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# -----------------------
# HOME
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})    