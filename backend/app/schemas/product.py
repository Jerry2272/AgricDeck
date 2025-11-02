from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.product import ProductCategory, ProductStatus


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: ProductCategory
    price_per_unit: float
    unit: str
    available_quantity: float
    freshness_level: Optional[str] = None
    location_state: Optional[str] = None
    location_city: Optional[str] = None
    is_seasonal: bool = False
    season_months: Optional[str] = None


class ProductCreate(ProductBase):
    harvest_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    image_urls: Optional[List[str]] = None
    
    @validator("available_quantity", "price_per_unit")
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    price_per_unit: Optional[float] = None
    unit: Optional[str] = None
    available_quantity: Optional[float] = None
    freshness_level: Optional[str] = None
    harvest_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    location_state: Optional[str] = None
    location_city: Optional[str] = None
    is_seasonal: Optional[bool] = None
    season_months: Optional[str] = None
    image_urls: Optional[List[str]] = None
    status: Optional[ProductStatus] = None


class ProductResponse(ProductBase):
    id: int
    farmer_id: int
    total_quantity: float
    status: ProductStatus
    is_verified: bool
    harvest_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    image_urls: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    id: int
    name: str
    category: ProductCategory
    price_per_unit: float
    unit: str
    available_quantity: float
    location_state: Optional[str] = None
    location_city: Optional[str] = None
    image_urls: Optional[List[str]] = None
    farmer_id: int
    farmer_name: Optional[str] = None
    
    class Config:
        from_attributes = True

