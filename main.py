from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os

from database import get_db, engine
from models import Base, User

# Routers
from auth import router as auth_router
from routers import (
    cart, products, seller, order, shop,
    payment, webhook, seller_profile,
    user_profile, subscription
)

# -----------------------------
# Templates
# -----------------------------
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Lifespan (DB table creation)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

# -----------------------------
# App init
# -----------------------------
app = FastAPI(lifespan=lifespan)

# Session middleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------
# Include routers (ONLY ONCE)
# -----------------------------
app.include_router(auth_router)
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

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):

    user_data = None

    try:
        user_id = request.session.get("user_id")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()

            if user:
                user_data = {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username
                }

    except Exception as e:
        print("Home Error:", e)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": user_data
        }
    )

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)