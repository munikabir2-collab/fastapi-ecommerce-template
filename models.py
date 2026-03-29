from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime

from datetime import datetime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy import Text, ForeignKey
from sqlalchemy.sql import func


from sqlalchemy.orm import relationship
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    description = Column(String)
    seller_id = Column(Integer, ForeignKey("users.id"))
    images = Column(String) 
    stock = Column(Integer, default=0)   # ✅ YAHAN ADD KARO
    seller = relationship("User")
    shop_id = Column(Integer, ForeignKey("shops.id"))
    gst_percent = Column(Float, default=18)



class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    product_name = Column(String)
    price = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    product = relationship("Product")  # ✅ Zaruri

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float, nullable=False)
    status = Column(String, default="PLACED")
    payment_method = Column(String)
    payment_status = Column(String, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Backrefs
    user = relationship(
        "User",
        back_populates="orders",
        foreign_keys=[user_id]
    )

    seller = relationship(
        "User",
        back_populates="sales",
        foreign_keys=[seller_id]
    )
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    role = Column(String, default="user")

    # 🔹 Explicit relationships to avoid ambiguity
    orders = relationship(
        "Order",
        back_populates="user",
        foreign_keys="[Order.user_id]"
    )

    sales = relationship(
        "Order",
        back_populates="seller",
        foreign_keys="[Order.seller_id]"
    )
    bank_account = relationship("SellerBank", uselist=False, back_populates="seller")

    

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order")
    product = relationship("Product")
    seller = relationship("User")
     # ✅ GST Fields
    gst_percent = Column(Float)
    hsn_code = Column(String)

    # snapshot
    product_name = Column(String)
    is_paid_to_seller = Column(Boolean, default=False)
     
    


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow) 
    shop_id = Column(Integer, ForeignKey("shops.id"))
   
    



class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), index=True)

    shop_name = Column(String)
    address = Column(String)
    webhook_url = Column(String)
    shop_description = Column(String)

    user = relationship("models.User")
    
    # ✅ GST Fields
    gst_no = Column(String)
    state = Column(String)
    pincode = Column(String)
    


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    plan = Column(String)              # free / basic / pro
    plan_id = Column(Integer, ForeignKey("plans.id"))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    shop_id = Column(Integer, ForeignKey("shops.id"))
class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    duration_days = Column(Integer)
    max_products = Column(Integer)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer)
    plan_id = Column(Integer)
    amount = Column(Integer)
    payment_method = Column(String)
    payment_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer)
    status = Column(String)
    message = Column(String)
    updated_by = Column(String, default="SYSTEM")  # SYSTEM, SELLER, DELIVERY_BOY
    created_at = Column(DateTime, default=datetime.utcnow)



class SellerBank(Base):
    __tablename__ = "seller_banks"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))

    name = Column(String)
    account_number = Column(String)
    ifsc = Column(String)
    bank_name = Column(String)
    beneficiary_id = Column(String, unique=True)

    # ✅ SAME indentation (no extra space)
    seller = relationship("User", back_populates="bank_account")
class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer)
    amount = Column(Float)
    commission = Column(Float)
    razorpay_payout_id = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)    