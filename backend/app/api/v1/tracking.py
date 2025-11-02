from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config.db import get_db
from app.core.auth.jwt import get_current_active_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.user import UserRole
from app.services.logistics import kwik
from typing import Optional

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.get("/orders/{order_id}")
async def track_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Track order status and delivery information"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Verify user is involved in order
    if current_user.id not in [order.buyer_id, order.farmer_id] and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this order"
        )
    
    tracking_info = {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "payment_status": order.payment_status.value,
        "delivery_type": order.delivery_type.value,
        "created_at": order.created_at,
        "estimated_delivery_date": order.estimated_delivery_date,
        "logistics_tracking_number": order.logistics_tracking_number,
        "logistics_partner": order.logistics_partner
    }
    
    # If order is shipped or in transit, get logistics tracking
    if order.logistics_tracking_number and order.logistics_partner == "kwik":
        try:
            logistics_tracking = await kwik.track_delivery(order.logistics_tracking_number)
            tracking_info["logistics"] = {
                "status": logistics_tracking.get("status"),
                "current_location": logistics_tracking.get("current_location"),
                "estimated_delivery": logistics_tracking.get("estimated_delivery"),
                "provider": logistics_tracking.get("provider")
            }
        except Exception as e:
            tracking_info["logistics"] = {
                "error": str(e),
                "provider": "kwik"
            }
    
    # Add status timeline
    tracking_info["timeline"] = {
        "pending": order.created_at if order.status == OrderStatus.PENDING else None,
        "accepted": order.accepted_at if order.status.value in ["accepted", "preparing", "shipped", "in_transit", "delivered"] else None,
        "shipped": order.shipped_at if order.status.value in ["shipped", "in_transit", "delivered"] else None,
        "delivered": order.delivered_at if order.status == OrderStatus.DELIVERED else None
    }
    
    return tracking_info


@router.get("/logistics/{tracking_number}")
async def track_logistics(
    tracking_number: str,
    provider: Optional[str] = "kwik",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Track delivery via logistics provider"""
    # Verify user has access to this tracking number
    order = db.query(Order).filter(Order.logistics_tracking_number == tracking_number).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    if current_user.id not in [order.buyer_id, order.farmer_id] and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to track this delivery"
        )
    
    # Get tracking info from logistics provider
    try:
        if provider == "kwik":
            tracking_info = await kwik.track_delivery(tracking_number)
            return tracking_info
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported logistics provider"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track delivery: {str(e)}"
        )

