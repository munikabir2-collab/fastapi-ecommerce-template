import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# safety check
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# fix postgres:// issue (Render compatibility)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# create engine
engine = create_engine(DATABASE_URL)

# session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base model
Base = declarative_base()

# dependency function (standard FastAPI way)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ alias for old code compatibility
fast_db = get_db