# main.py
from fastapi import FastAPI, Request, Depends
import models
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database import engine, Base, fast_db, get_db
from auth import router as auth_router
import os
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
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

#templates = Jinja2Templates(directory="templates")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

templates.env.cache = {}   # 🔥 IMPORTANT FIX
templates.env.auto_reload = True   # ✅ add this
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

print("CHECK DB:", os.getenv("DATABASE_URL"))
# -----------------------
# HOME
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):  # use get_db, not fast_db

    user = db.query(models.User).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request}
        )

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
            
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)    