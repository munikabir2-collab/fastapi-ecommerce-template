from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from auth import router as auth_router
from database import get_db
from models import User
from templates import templates

# Other routers
from routers import (
    cart, products, seller, order, shop,
    payment, webhook, seller_profile, user_profile, subscription
)

load_dotenv(dotenv_path=".env", override=True)

app = FastAPI(debug=True)

# Middleware
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Templates

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
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


# Home route
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    context = {"request": request}

    user = db.query(User).first()

    if user:
        context["user"] = {
            "id": user.id,
            "name": user.name
        }

    return templates.TemplateResponse("login.html", context)
# Run local
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)