from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates

from database import SessionLocal
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# DB session dependency
def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Serializer for Plan
# -------------------------
def serialize_plan(plan):
    if not plan:
        return {}
    return {
        "id": getattr(plan, "id", None),
        "name": getattr(plan, "name", "N/A"),
        "price": float(getattr(plan, "price", 0)),
        "duration_days": getattr(plan, "duration_days", 30),
        "max_products": getattr(plan, "max_products", 0),
    }


# ===============================
# SHOW ALL PLANS
# ===============================
@router.get("/plans")
def show_plans(request: Request, db: Session = Depends(fast_db)):
    plans = db.query(models.Plan).all()
    plans_serialized = [serialize_plan(p) for p in plans]

    return templates.TemplateResponse(
        "plans.html",
        {
            "request": request,
            "plans": plans_serialized
        }
    )


# ===============================
# SUBSCRIBE PLAN
# ===============================
@router.get("/subscribe/{plan_id}")
def subscribe_plan(request: Request, plan_id: int, db: Session = Depends(fast_db)):

    # session-based user check
    seller_id = request.session.get("user_id")
    if not seller_id:
        return RedirectResponse("/login", status_code=303)

    # fetch plan safely
    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not plan:
        return {"error": "Plan not found"}

    start = datetime.utcnow()
    duration = getattr(plan, "duration_days", 30)
    end = start + timedelta(days=duration)

    subscription = models.Subscription(
        seller_id=seller_id,
        plan_id=getattr(plan, "id", None),
        plan=getattr(plan, "name", "N/A"),
        expires_at=end,
        is_active=True
    )

    db.add(subscription)
    db.commit()

    return RedirectResponse("/seller/dashboard", status_code=303)