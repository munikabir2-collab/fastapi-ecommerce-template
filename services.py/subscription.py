from fastapi import HTTPException
from models.subscription_model import Subscription
from models.plan_model import Plan
from models.product_model import Product


def check_product_limit(db, seller_id):

    # seller subscription check
    sub = db.query(Subscription).filter(
        Subscription.seller_id == seller_id,
        Subscription.is_active == True
    ).first()

    if not sub:
        raise HTTPException(status_code=403, detail="Subscription expired")

    # plan fetch
    plan = db.query(Plan).filter(
        Plan.id == sub.plan_id
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # seller product count
    product_count = db.query(Product).filter(
        Product.seller_id == seller_id
    ).count()

    # limit check
    if product_count >= plan.max_products:
        raise HTTPException(
            status_code=403,
            detail="Product limit reached. Please upgrade plan."
        )

    return True