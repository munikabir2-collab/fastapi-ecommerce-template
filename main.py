from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os

# Auth & DB
from auth import router as auth_router
from database import get_db
from models import User, Base
from database import engine

# Routers
from routers import (
    cart, products, seller, order, shop,
    payment, webhook, seller_profile, user_profile, subscription
)

# Load env
load_dotenv(dotenv_path=".env", override=True)

# ==============================
# LIFESPAN (NEW FASTAPI WAY)
# ==============================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables on startup
    Base.metadata.create_all(bind=engine)
    yield


# ==============================
# APP INIT
# ==============================
app = FastAPI(lifespan=lifespan, debug=True)

# Middleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==============================
# ROUTERS
# ==============================
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


# ==============================
# HOME ROUTE
# ==============================
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):

    user_data = None

    try:
        user = db.query(User).first()

        if user:
            user_data = {
                "id": user.id,
                "name": user.name
            }

    except Exception as e:
        print("Database Error:", e)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": user_data
        }
    )


# ==============================
# RUN LOCALLY
# ==============================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


    