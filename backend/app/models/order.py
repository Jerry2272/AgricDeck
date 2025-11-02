from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.config.db import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"  # Buyer placed order, awaiting farmer acceptance
    ACCEPTED = "accepted"  # Farmer accepted order
    REJECTED = "rejected"  # Farmer rejected order
    PREPARING = "preparing"  # Farmer preparing order
    SHIPPED = "shipped"  # Order shipped/dispatched
    IN_TRANSIT = "in_transit"  # Order in transit
    DELIVERED = "delivered"  # Order delivered
    CANCELLED = "cancelled"  # Order cancelled
    DISPUTED = "disputed"  # Order in dispute


class DeliveryType(str, enum.Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # User relationships
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order details
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    delivery_type = Column(Enum(DeliveryType), nullable=False)
    
    # Pricing
    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Payment
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=True)  # card, bank_transfer, ussd, wallet
    payment_reference = Column(String(100), nullable=True)
    payment_gateway = Column(String(50), nullable=True)  # paystack, flutterwave
    
    # Delivery information
    delivery_address = Column(Text, nullable=True)
    delivery_state = Column(String(100), nullable=True)
    delivery_city = Column(String(100), nullable=True)
    delivery_phone = Column(String(20), nullable=True)
    delivery_instructions = Column(Text, nullable=True)
    
    # Pickup information
    pickup_address = Column(Text, nullable=True)
    pickup_phone = Column(String(20), nullable=True)
    
    # Logistics
    logistics_partner = Column(String(100), nullable=True)  # kwik, gig, etc.
    logistics_tracking_number = Column(String(100), nullable=True)
    logistics_order_id = Column(String(100), nullable=True)
    estimated_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    buyer_notes = Column(Text, nullable=True)
    farmer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_buyer")
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="orders_farmer")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment_transactions = relationship("PaymentTransaction", back_populates="order")
    dispute = relationship("Dispute", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    product_name = Column(String(200), nullable=False)  # Snapshot at time of order
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

