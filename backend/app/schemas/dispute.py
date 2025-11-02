from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.dispute import DisputeStatus, DisputeType


class DisputeCreate(BaseModel):
    order_id: int
    dispute_type: DisputeType
    description: str


class DisputeUpdate(BaseModel):
    status: Optional[DisputeStatus] = None
    resolution: Optional[str] = None
    admin_notes: Optional[str] = None


class DisputeResponse(BaseModel):
    id: int
    order_id: int
    raised_by_id: int
    disputed_user_id: int
    dispute_type: DisputeType
    status: DisputeStatus
    description: str
    resolution: Optional[str] = None
    handled_by: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

