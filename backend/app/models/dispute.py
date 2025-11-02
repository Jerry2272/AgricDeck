from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.config.db import Base


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputeType(str, enum.Enum):
    PRODUCT_QUALITY = "product_quality"
    DELIVERY_ISSUE = "delivery_issue"
    PAYMENT_ISSUE = "payment_issue"
    OTHER = "other"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    
    raised_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    disputed_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    dispute_type = Column(Enum(DisputeType), nullable=False)
    status = Column(Enum(DisputeStatus), default=DisputeStatus.OPEN)
    
    description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    
    # Admin handling
    handled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    handled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="dispute")
    raised_by = relationship("User", foreign_keys=[raised_by_id])
    disputed_user = relationship("User", foreign_keys=[disputed_user_id])

