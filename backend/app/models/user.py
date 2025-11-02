from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.config.db import Base


class UserRole(str, enum.Enum):
    BUYER = "buyer"
    FARMER = "farmer"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.BUYER)
    
    # KYC & Verification
    is_verified = Column(Boolean, default=False)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_document_url = Column(String(500), nullable=True)
    
    # Farmer-specific fields
    farm_name = Column(String(200), nullable=True)
    farm_address = Column(Text, nullable=True)
    farm_location_state = Column(String(100), nullable=True)
    farm_location_city = Column(String(100), nullable=True)
    farm_location_coordinates = Column(String(100), nullable=True)  # lat,lng
    bank_account_number = Column(String(20), nullable=True)
    bank_name = Column(String(100), nullable=True)
    account_name = Column(String(200), nullable=True)
    
    # Wallet & Earnings
    wallet_balance = Column(Float, default=0.0)
    
    # Profile
    profile_image_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="farmer", cascade="all, delete-orphan")
    orders_buyer = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    orders_farmer = relationship("Order", foreign_keys="Order.farmer_id", back_populates="farmer")
    reviews_given = relationship("Review", foreign_keys="Review.buyer_id", back_populates="buyer")
    reviews_received = relationship("Review", foreign_keys="Review.farmer_id", back_populates="farmer")
    cart_items = relationship("CartItem", back_populates="buyer", cascade="all, delete-orphan")
    withdrawals = relationship("Withdrawal", back_populates="farmer", cascade="all, delete-orphan")

