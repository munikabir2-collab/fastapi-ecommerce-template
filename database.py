import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# =========================================
# LOAD ENV VARIABLES
# =========================================

load_dotenv()

# =========================================
# DATABASE URL
# =========================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing")

# =========================================
# FIX RENDER POSTGRES URL
# =========================================

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# =========================================
# ENGINE
# =========================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# =========================================
# SESSION
# =========================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =========================================
# BASE
# =========================================

Base = declarative_base()

# =========================================
# FASTAPI DB DEPENDENCY
# =========================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# OLD CODE SUPPORT
fast_db = get_db