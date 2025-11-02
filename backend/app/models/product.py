from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.config.db import Base


class ProductCategory(str, enum.Enum):
    GRAINS = "grains"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    TUBERS = "tubers"
    LEGUMES = "legumes"
    SPICES = "spices"
    OTHER = "other"


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD_OUT = "sold_out"
    SUSPENDED = "suspended"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(ProductCategory), nullable=False)
    
    # Pricing
    price_per_unit = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # kg, bag, bunch, etc.
    
    # Inventory
    available_quantity = Column(Float, nullable=False, default=0.0)
    total_quantity = Column(Float, nullable=False, default=0.0)
    
    # Product Details
    freshness_level = Column(String(50), nullable=True)  # fresh, organic, etc.
    harvest_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Images
    image_urls = Column(Text, nullable=True)  # JSON array of image URLs
    
    # Status
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    is_verified = Column(Boolean, default=False)
    
    # Location
    location_state = Column(String(100), nullable=True)
    location_city = Column(String(100), nullable=True)
    
    # Seasonality
    is_seasonal = Column(Boolean, default=False)
    season_months = Column(String(100), nullable=True)  # "jan,feb,mar"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    farmer = relationship("User", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")

