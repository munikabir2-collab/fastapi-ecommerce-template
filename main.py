from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from models import User   
import models
from database import get_db   # ✅ only needed import
from auth import router as auth_router

# Routers
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
print(type("login.html"))  # should be str
load_dotenv(dotenv_path=".env", override=True)


# -----------------------
# LOAD ENV
# -----------------------


# -----------------------
# APP SETUP
# -----------------------
app = FastAPI(debug=True)

app.add_middleware(
    SessionMiddleware,
    secret_key="supersecretkey"
)

# ❌ REMOVE THIS (causes crash on Render)
#from database import engine, Base
#Base.metadata.create_all(bind=engine)

# -----------------------
# TEMPLATE SETUP
# -----------------------
templates = Jinja2Templates(directory="templates")
# -----------------------
# STATIC FILES
# -----------------------
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
# -----------------------
# ROUTERS
# -----------------------
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

# -----------------------
# HOME ROUTE
# -----------------------
# main.py
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = db.query(User).first()
    context = {"request": request}

    if user:
        context["user"] = user.to_dict()  # Convert model to dict

    return templates.TemplateResponse("login.html", context)
# -----------------------
# RUN LOCAL
# -----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)