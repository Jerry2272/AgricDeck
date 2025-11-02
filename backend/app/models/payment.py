from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.config.db import Base


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"
    COMMISSION = "commission"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Gateway details
    gateway = Column(String(50), nullable=False)  # paystack, flutterwave
    gateway_reference = Column(String(100), unique=True, nullable=True)
    gateway_response = Column(Text, nullable=True)  # JSON response
    
    # Payment method
    payment_method = Column(String(50), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payment_transactions")
    user = relationship("User")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Bank details
    bank_account_number = Column(String(20), nullable=False)
    bank_name = Column(String(100), nullable=False)
    account_name = Column(String(200), nullable=False)
    
    # Gateway processing
    gateway = Column(String(50), nullable=True)  # paystack, flutterwave
    gateway_reference = Column(String(100), nullable=True)
    gateway_response = Column(Text, nullable=True)
    
    # Admin
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farmer = relationship("User", back_populates="withdrawals")

