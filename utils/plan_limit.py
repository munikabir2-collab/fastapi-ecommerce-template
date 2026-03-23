from fastapi import HTTPException
from models import Subscription, Plan, Product

def check_product_limit(db, seller_id):

    sub = db.query(Subscription).filter(
        Subscription.seller_id == seller_id,
        Subscription.is_active == True
    ).first()

    if not sub:
        raise HTTPException(status_code=403, detail="No active plan")

    plan = db.query(Plan).filter(
        Plan.id == sub.plan_id
    ).first()

    product_count = db.query(Product).filter(
        Product.seller_id == seller_id
    ).count()

    if product_count >= plan.product_limit:
        raise HTTPException(
            status_code=403,
            detail="Product limit reached. Please upgrade your plan."
        )