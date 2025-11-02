from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    order_id: int
    rating: int
    comment: Optional[str] = None
    
    @validator("rating")
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    id: int
    order_id: int
    buyer_id: int
    farmer_id: int
    rating: int
    comment: Optional[str] = None
    buyer_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FarmerRatingResponse(BaseModel):
    farmer_id: int
    average_rating: float
    total_reviews: int
    reviews: list[ReviewResponse] = []

