from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.order import OrderStatus, DeliveryType, PaymentStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float
    
    @validator("quantity")
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class OrderCreate(BaseModel):
    delivery_type: DeliveryType
    delivery_address: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_phone: Optional[str] = None
    delivery_instructions: Optional[str] = None
    pickup_address: Optional[str] = None
    pickup_phone: Optional[str] = None
    buyer_notes: Optional[str] = None
    items: List[OrderItemCreate]
    
    @validator("delivery_address", "pickup_address")
    def validate_address(cls, v, values):
        delivery_type = values.get("delivery_type")
        if delivery_type == DeliveryType.DELIVERY and not v:
            raise ValueError("Delivery address is required for delivery orders")
        elif delivery_type == DeliveryType.PICKUP and not values.get("pickup_address"):
            raise ValueError("Pickup address is required for pickup orders")
        return v


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    buyer_id: int
    farmer_id: int
    status: OrderStatus
    delivery_type: DeliveryType
    subtotal: float
    delivery_fee: float
    commission: float
    total_amount: float
    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    logistics_tracking_number: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    farmer_notes: Optional[str] = None


class OrderListResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    total_amount: float
    delivery_type: DeliveryType
    created_at: datetime
    farmer_name: Optional[str] = None
    buyer_name: Optional[str] = None
    
    class Config:
        from_attributes = True

