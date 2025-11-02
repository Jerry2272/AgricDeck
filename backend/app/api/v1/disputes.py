from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.config.db import get_db
from app.core.auth.jwt import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.dispute import Dispute, DisputeStatus
from app.schemas.dispute import DisputeCreate, DisputeUpdate, DisputeResponse

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_data: DisputeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new dispute for an order"""
    # Get order
    order = db.query(Order).filter(Order.id == dispute_data.order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify user is involved in order
    if current_user.id not in [order.buyer_id, order.farmer_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create a dispute for this order"
        )
    
    # Check if dispute already exists
    existing_dispute = db.query(Dispute).filter(Dispute.order_id == dispute_data.order_id).first()
    if existing_dispute:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispute already exists for this order"
        )
    
    # Determine disputed user (the other party)
    if current_user.id == order.buyer_id:
        disputed_user_id = order.farmer_id
    else:
        disputed_user_id = order.buyer_id
    
    # Create dispute
    dispute = Dispute(
        order_id=dispute_data.order_id,
        raised_by_id=current_user.id,
        disputed_user_id=disputed_user_id,
        dispute_type=dispute_data.dispute_type,
        status=DisputeStatus.OPEN,
        description=dispute_data.description
    )
    
    # Update order status
    order.status = OrderStatus.DISPUTED
    
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    
    return dispute


@router.get("/", response_model=List[DisputeResponse])
async def get_my_disputes(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get disputes where user is involved"""
    disputes = db.query(Dispute).filter(
        (Dispute.raised_by_id == current_user.id) |
        (Dispute.disputed_user_id == current_user.id)
    ).order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()
    
    return disputes


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific dispute"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Verify user is involved
    if current_user.id not in [dispute.raised_by_id, dispute.disputed_user_id] and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this dispute"
        )
    
    return dispute


@router.put("/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: int,
    dispute_data: DisputeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a dispute (only admin can update status)"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Only admin can update dispute status
    if dispute_data.status and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update dispute status"
        )
    
    # Update fields
    update_data = dispute_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dispute, field, value)
    
    if dispute_data.status == DisputeStatus.RESOLVED:
        from datetime import datetime
        dispute.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(dispute)
    
    return dispute

