from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates

from database import SessionLocal
import models

router = APIRouter()
#templates = Jinja2Templates(directory="templates")


def fast_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===============================
# SHOW ALL PLANS
# ===============================

@router.get("/plans")
def show_plans(request: Request, db: Session = Depends(fast_db)):

    plans = db.query(models.Plan).all()

    return request.app.state.templates.TemplateResponse(
        "plans.html",
        {
            "request": request,
            "plans": plans
        }
    )


# ===============================
# SUBSCRIBE PLAN
# ===============================

@router.get("/subscribe/{plan_id}")
def subscribe_plan(request: Request, plan_id: int, db: Session = Depends(fast_db)):

    seller_id = request.session.get("user_id")

    if not seller_id:
        return RedirectResponse("/login", status_code=303)

    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()

    if not plan:
        return {"error": "Plan not found"}

    start = datetime.utcnow()

    duration = plan.duration_days if plan.duration_days else 30

    end = start + timedelta(days=duration)

    subscription = models.Subscription(
        seller_id=seller_id,
        plan_id=plan.id,
        plan=plan.name,
        expires_at=end,
        is_active=True
    )

    db.add(subscription)
    db.commit()

    return RedirectResponse("/seller/dashboard", status_code=303)