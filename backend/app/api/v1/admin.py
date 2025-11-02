from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from app.core.config.db import get_db
from app.core.auth.jwt import require_role
from app.models.user import User, UserRole, VerificationStatus
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import PaymentTransaction, Withdrawal, TransactionStatus
from app.models.dispute import Dispute, DisputeStatus, DisputeType
from app.models.review import Review
from app.schemas.dispute import DisputeCreate, DisputeUpdate, DisputeResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    # Users stats
    total_users = db.query(User).count()
    total_farmers = db.query(User).filter(User.role == UserRole.FARMER).count()
    total_buyers = db.query(User).filter(User.role == UserRole.BUYER).count()
    pending_farmer_verifications = db.query(User).filter(
        User.role == UserRole.FARMER,
        User.verification_status == VerificationStatus.PENDING
    ).count()
    
    # Orders stats
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    delivered_orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).count()
    
    # Revenue stats
    delivered_orders_with_payment = db.query(Order).filter(
        Order.status == OrderStatus.DELIVERED,
        Order.payment_status == PaymentStatus.PAID
    ).all()
    
    total_revenue = sum(order.total_amount for order in delivered_orders_with_payment)
    total_commission = sum(order.commission for order in delivered_orders_with_payment)
    
    # Products stats
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
    suspended_products = db.query(Product).filter(Product.status == ProductStatus.SUSPENDED).count()
    
    # Disputes stats
    open_disputes = db.query(Dispute).filter(Dispute.status == DisputeStatus.OPEN).count()
    under_review_disputes = db.query(Dispute).filter(Dispute.status == DisputeStatus.UNDER_REVIEW).count()
    
    # Recent transactions
    recent_transactions = db.query(PaymentTransaction).order_by(
        PaymentTransaction.created_at.desc()
    ).limit(10).all()
    
    return {
        "users": {
            "total": total_users,
            "farmers": total_farmers,
            "buyers": total_buyers,
            "pending_farmer_verifications": pending_farmer_verifications
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "delivered": delivered_orders
        },
        "revenue": {
            "total": total_revenue,
            "commission": total_commission
        },
        "products": {
            "total": total_products,
            "active": active_products,
            "suspended": suspended_products
        },
        "disputes": {
            "open": open_disputes,
            "under_review": under_review_disputes
        },
        "recent_transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "status": t.status.value,
                "created_at": t.created_at
            } for t in recent_transactions
        ]
    }


@router.get("/farmers/pending", response_model=List[dict])
async def get_pending_farmers(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get farmers pending verification"""
    farmers = db.query(User).filter(
        User.role == UserRole.FARMER,
        User.verification_status == VerificationStatus.PENDING
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": f.id,
            "email": f.email,
            "phone": f.phone,
            "first_name": f.first_name,
            "last_name": f.last_name,
            "farm_name": f.farm_name,
            "farm_location_state": f.farm_location_state,
            "farm_location_city": f.farm_location_city,
            "verification_document_url": f.verification_document_url,
            "created_at": f.created_at
        } for f in farmers
    ]


@router.put("/farmers/{farmer_id}/verify")
async def verify_farmer(
    farmer_id: int,
    approve: bool = True,
    notes: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Approve or reject farmer verification"""
    farmer = db.query(User).filter(
        User.id == farmer_id,
        User.role == UserRole.FARMER
    ).first()
    
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found"
        )
    
    if approve:
        farmer.verification_status = VerificationStatus.APPROVED
        farmer.is_verified = True
    else:
        farmer.verification_status = VerificationStatus.REJECTED
        farmer.is_verified = False
    
    # Store admin notes if needed (could add admin_notes field to User model)
    db.commit()
    db.refresh(farmer)
    
    return {
        "message": "Farmer verified" if approve else "Farmer verification rejected",
        "farmer": {
            "id": farmer.id,
            "verification_status": farmer.verification_status.value,
            "is_verified": farmer.is_verified
        }
    }


@router.get("/products")
async def get_products_for_moderation(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[ProductStatus] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get products for moderation"""
    query = db.query(Product)
    
    if status_filter:
        query = query.filter(Product.status == status_filter)
    
    products = query.offset(skip).limit(limit).all()
    
    result = []
    for product in products:
        farmer = db.query(User).filter(User.id == product.farmer_id).first()
        result.append({
            "id": product.id,
            "name": product.name,
            "category": product.category.value,
            "price_per_unit": product.price_per_unit,
            "status": product.status.value,
            "farmer_id": product.farmer_id,
            "farmer_name": f"{farmer.first_name} {farmer.last_name}" if farmer else None,
            "created_at": product.created_at
        })
    
    return result


@router.put("/products/{product_id}/status")
async def update_product_status(
    product_id: int,
    new_status: ProductStatus,
    notes: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Suspend or activate a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.status = new_status
    
    db.commit()
    db.refresh(product)
    
    return {
        "message": f"Product status updated to {new_status.value}",
        "product": {
            "id": product.id,
            "name": product.name,
            "status": product.status.value
        }
    }


@router.get("/orders")
async def get_all_orders(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[OrderStatus] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all orders for admin"""
    query = db.query(Order)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        buyer = db.query(User).filter(User.id == order.buyer_id).first()
        farmer = db.query(User).filter(User.id == order.farmer_id).first()
        
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "total_amount": order.total_amount,
            "buyer_name": f"{buyer.first_name} {buyer.last_name}" if buyer else None,
            "farmer_name": f"{farmer.first_name} {farmer.last_name}" if farmer else None,
            "created_at": order.created_at
        })
    
    return result


@router.get("/disputes")
async def get_disputes(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[DisputeStatus] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all disputes"""
    query = db.query(Dispute)
    
    if status_filter:
        query = query.filter(Dispute.status == status_filter)
    
    disputes = query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for dispute in disputes:
        raised_by = db.query(User).filter(User.id == dispute.raised_by_id).first()
        disputed_user = db.query(User).filter(User.id == dispute.disputed_user_id).first()
        order = db.query(Order).filter(Order.id == dispute.order_id).first()
        
        result.append({
            "id": dispute.id,
            "order_id": dispute.order_id,
            "order_number": order.order_number if order else None,
            "dispute_type": dispute.dispute_type.value,
            "status": dispute.status.value,
            "description": dispute.description,
            "resolution": dispute.resolution,
            "raised_by": f"{raised_by.first_name} {raised_by.last_name}" if raised_by else None,
            "disputed_user": f"{disputed_user.first_name} {disputed_user.last_name}" if disputed_user else None,
            "created_at": dispute.created_at,
            "resolved_at": dispute.resolved_at
        })
    
    return result


@router.put("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: int,
    resolution: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Resolve a dispute"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = resolution
    dispute.resolved_at = datetime.utcnow()
    dispute.handled_by = current_user.id
    dispute.handled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(dispute)
    
    return {
        "message": "Dispute resolved",
        "dispute": {
            "id": dispute.id,
            "status": dispute.status.value,
            "resolution": dispute.resolution,
            "resolved_at": dispute.resolved_at
        }
    }


@router.get("/withdrawals")
async def get_withdrawals(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[TransactionStatus] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all withdrawal requests"""
    query = db.query(Withdrawal)
    
    if status_filter:
        query = query.filter(Withdrawal.status == status_filter)
    
    withdrawals = query.order_by(Withdrawal.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for withdrawal in withdrawals:
        farmer = db.query(User).filter(User.id == withdrawal.farmer_id).first()
        
        result.append({
            "id": withdrawal.id,
            "farmer_id": withdrawal.farmer_id,
            "farmer_name": f"{farmer.first_name} {farmer.last_name}" if farmer else None,
            "amount": withdrawal.amount,
            "status": withdrawal.status.value,
            "bank_account_number": withdrawal.bank_account_number,
            "bank_name": withdrawal.bank_name,
            "account_name": withdrawal.account_name,
            "created_at": withdrawal.created_at,
            "processed_at": withdrawal.processed_at
        })
    
    return result


@router.put("/withdrawals/{withdrawal_id}/process")
async def process_withdrawal(
    withdrawal_id: int,
    approve: bool = True,
    gateway: str = "paystack",
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Process a withdrawal request"""
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).first()
    
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    if withdrawal.status != TransactionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal already processed"
        )
    
    farmer = db.query(User).filter(User.id == withdrawal.farmer_id).first()
    
    if approve:
        # Process withdrawal via gateway
        try:
            from app.services.payment import paystack, flutterwave
            
            if gateway == "paystack":
                # First create recipient
                recipient = await paystack.create_transfer_recipient(
                    account_number=withdrawal.bank_account_number,
                    bank_code="",  # Need bank code mapping
                    account_name=withdrawal.account_name
                )
                recipient_code = recipient.get("data", {}).get("recipient_code")
                
                # Then initiate transfer
                transfer = await paystack.initiate_transfer(
                    recipient_code=recipient_code,
                    amount=withdrawal.amount,
                    reference=f"WD-{withdrawal.id}",
                    reason="Farmer withdrawal"
                )
                
                withdrawal.gateway = "paystack"
                withdrawal.gateway_reference = transfer.get("data", {}).get("reference")
                withdrawal.status = TransactionStatus.SUCCESS
            else:
                # Flutterwave
                transfer = await flutterwave.initiate_transfer(
                    account_number=withdrawal.bank_account_number,
                    bank_code="",  # Need bank code mapping
                    amount=withdrawal.amount,
                    reference=f"WD-{withdrawal.id}",
                    narration="Farmer withdrawal"
                )
                
                withdrawal.gateway = "flutterwave"
                withdrawal.gateway_reference = transfer.get("data", {}).get("reference")
                withdrawal.status = TransactionStatus.SUCCESS
            
            # Deduct from farmer wallet
            farmer.wallet_balance -= withdrawal.amount
            
            withdrawal.processed_by = current_user.id
            withdrawal.processed_at = datetime.utcnow()
        except Exception as e:
            withdrawal.status = TransactionStatus.FAILED
            withdrawal.admin_notes = f"Processing failed: {str(e)}"
    else:
        withdrawal.status = TransactionStatus.CANCELLED
        withdrawal.processed_by = current_user.id
        withdrawal.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(withdrawal)
    
    return {
        "message": "Withdrawal processed" if approve else "Withdrawal cancelled",
        "withdrawal": {
            "id": withdrawal.id,
            "status": withdrawal.status.value,
            "processed_at": withdrawal.processed_at
        }
    }


@router.get("/transactions")
async def get_all_transactions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all payment transactions"""
    transactions = db.query(PaymentTransaction).order_by(
        PaymentTransaction.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for transaction in transactions:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        
        result.append({
            "id": transaction.id,
            "order_id": transaction.order_id,
            "user_id": transaction.user_id,
            "user_name": f"{user.first_name} {user.last_name}" if user else None,
            "transaction_type": transaction.transaction_type.value,
            "amount": transaction.amount,
            "status": transaction.status.value,
            "gateway": transaction.gateway,
            "created_at": transaction.created_at
        })
    
    return result

