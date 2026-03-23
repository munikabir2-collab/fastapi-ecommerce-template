# dependencies.py
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import fast_db
from models import User

def get_current_user(
    request: Request,
    db: Session = Depends(fast_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
