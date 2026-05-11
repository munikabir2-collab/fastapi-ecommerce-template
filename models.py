from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    Boolean, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


# =========================
# USER MODEL
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    address = Column(String(255))
    state = Column(String(100))
    pincode = Column(String(10))
    role = Column(String(20), default="user")  # user / seller / admin

    # relationships
    orders = relationship(
        "Order",
        foreign_keys="Order.user_id",
        back_populates="user"
    )

    sales = relationship(
        "Order",
        foreign_keys="Order.seller_id",
        back_populates="seller"
    )

    bank_account = relationship(
        "SellerBank",
        uselist=False,
        back_populates="seller"
    )


# =========================
# PRODUCT
# =========================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    description = Column(String)
    images = Column(String)

    stock = Column(Integer, default=0)
    gst_percent = Column(Float, default=18)

    seller_id = Column(Integer, ForeignKey("users.id"))
    shop_id = Column(Integer, ForeignKey("shops.id"))

    seller = relationship("User")


# =========================
# CART
# =========================
class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    product_name = Column(String)   # ✅ ADD THIS
    quantity = Column(Integer, default=1)

    product = relationship("Product")
    price = Column(Float)   # ✅ add this 

# =========================
# ORDER
# =========================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"))

    total = Column(Float, nullable=False)
    invoice_number = Column(String, nullable=True)   # ✅ ADD THIS 
    status = Column(String, default="PLACED")
    payment_method = Column(String)
    payment_status = Column(String, default="PENDING")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="orders"
    )

    seller = relationship(
        "User",
        foreign_keys=[seller_id],
        back_populates="sales"
    )

    order_items = relationship("OrderItem", back_populates="order")


# =========================
# ORDER ITEM
# =========================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))

    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    gst_percent = Column(Float)
    hsn_code = Column(String)

    product_name = Column(String)
    is_paid_to_seller = Column(Boolean, default=False)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")
    seller = relationship("User")


# =========================
# NOTIFICATION
# =========================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    seller_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String)
    message = Column(String)

    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# SHOP
# =========================
class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True)

    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))


# =========================
# SELLER PROFILE
# =========================
class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(Integer, primary_key=True, index=True)

    seller_id = Column(Integer, ForeignKey("users.id"), index=True)

    shop_name = Column(String)
    address = Column(String)
    webhook_url = Column(String)
    shop_description = Column(String)

    gst_no = Column(String)
    state = Column(String)
    pincode = Column(String)

    user = relationship("User")


# =========================
# SUBSCRIPTION
# =========================
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)

    seller_id = Column(Integer, ForeignKey("users.id"))
    plan = Column(String)
    plan_id = Column(Integer, ForeignKey("plans.id"))

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    shop_id = Column(Integer, ForeignKey("shops.id"))


# =========================
# PLAN
# =========================
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)

    name = Column(String)
    price = Column(Integer)
    duration_days = Column(Integer)
    max_products = Column(Integer)


# =========================
# PAYMENT
# =========================
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    seller_id = Column(Integer)
    plan_id = Column(Integer)

    amount = Column(Integer)
    payment_method = Column(String)
    payment_status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# ORDER TRACKING
# =========================
class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer)
    status = Column(String)
    message = Column(String)

    updated_by = Column(String, default="SYSTEM")

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# SELLER BANK
# =========================
class SellerBank(Base):
    __tablename__ = "seller_banks"

    id = Column(Integer, primary_key=True, index=True)

    seller_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String)
    account_number = Column(String)
    ifsc = Column(String)
    bank_name = Column(String)

    beneficiary_id = Column(String, unique=True)

    seller = relationship("User", back_populates="bank_account")


# =========================
# PAYOUT
# =========================
class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)

    seller_id = Column(Integer)

    amount = Column(Float)
    commission = Column(Float)

    razorpay_payout_id = Column(String)
    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)