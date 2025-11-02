from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.product import ProductListItem


class CartItemCreate(BaseModel):
    product_id: int
    quantity: float


class CartItemUpdate(BaseModel):
    quantity: float


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    product: ProductListItem
    created_at: datetime
    
    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    subtotal: float

