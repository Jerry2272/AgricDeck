from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.core.config.db import get_db
from app.core.auth.jwt import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus, ProductCategory
from app.models.order import Order, OrderStatus, OrderItem, DeliveryType, PaymentStatus
from app.models.payment import Withdrawal, TransactionStatus
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.order import OrderResponse, OrderListResponse, OrderStatusUpdate
from app.schemas.payment import WithdrawalRequest, WithdrawalResponse
from app.schemas.user import FarmerProfileUpdate
from datetime import datetime
import uuid

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.get("/products", response_model=List[ProductResponse])
async def get_my_products(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Get all products listed by current farmer"""
    products = db.query(Product).filter(
        Product.farmer_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return products


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Create a new product listing"""
    # Import json for image_urls
    import json
    
    product = Product(
        farmer_id=current_user.id,
        name=product_data.name,
        description=product_data.description,
        category=product_data.category,
        price_per_unit=product_data.price_per_unit,
        unit=product_data.unit,
        available_quantity=product_data.available_quantity,
        total_quantity=product_data.available_quantity,
        freshness_level=product_data.freshness_level,
        harvest_date=product_data.harvest_date,
        expiry_date=product_data.expiry_date,
        location_state=product_data.location_state or current_user.farm_location_state,
        location_city=product_data.location_city or current_user.farm_location_city,
        is_seasonal=product_data.is_seasonal,
        season_months=product_data.season_months,
        image_urls=json.dumps(product_data.image_urls) if product_data.image_urls else None,
        status=ProductStatus.ACTIVE
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Get a specific product by ID"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.farmer_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Update a product listing"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.farmer_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    import json
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    if "image_urls" in update_data and update_data["image_urls"]:
        update_data["image_urls"] = json.dumps(update_data["image_urls"])
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    if "available_quantity" in update_data:
        product.total_quantity = max(product.total_quantity, update_data["available_quantity"])
        if update_data["available_quantity"] <= 0:
            product.status = ProductStatus.SOLD_OUT
    
    db.commit()
    db.refresh(product)
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Delete a product listing"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.farmer_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(product)
    db.commit()


@router.get("/orders", response_model=List[OrderListResponse])
async def get_my_orders(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[OrderStatus] = None,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Get all orders for current farmer"""
    query = db.query(Order).filter(Order.farmer_id == current_user.id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.farmer_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Update order status (accept/reject/prepare/ship)"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.farmer_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate status transitions
    if order.status == OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a delivered order"
        )
    
    if status_update.status == OrderStatus.ACCEPTED and order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only accept pending orders"
        )
    
    # Update order
    order.status = status_update.status
    order.farmer_notes = status_update.farmer_notes
    
    if status_update.status == OrderStatus.ACCEPTED:
        order.accepted_at = datetime.utcnow()
        # Update inventory
        for item in order.order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.available_quantity -= item.quantity
                if product.available_quantity <= 0:
                    product.status = ProductStatus.SOLD_OUT
    
    elif status_update.status == OrderStatus.SHIPPED:
        order.shipped_at = datetime.utcnow()
        
        # If delivery type is DELIVERY, create logistics order
        if order.delivery_type == DeliveryType.DELIVERY and not order.logistics_tracking_number:
            from app.services.logistics.kwik import create_delivery_order
            from app.models.user import User as UserModel
            
            # Get farmer and buyer info
            farmer_user = db.query(UserModel).filter(UserModel.id == order.farmer_id).first()
            buyer_user = db.query(UserModel).filter(UserModel.id == order.buyer_id).first()
            
            if farmer_user and buyer_user:
                try:
                    # Create delivery order with logistics partner
                    logistics_result = await create_delivery_order(
                        pickup_address=order.pickup_address or farmer_user.farm_address or "",
                        delivery_address=order.delivery_address or "",
                        pickup_phone=order.pickup_phone or farmer_user.phone,
                        delivery_phone=order.delivery_phone or buyer_user.phone,
                        pickup_name=f"{farmer_user.first_name} {farmer_user.last_name}",
                        delivery_name=f"{buyer_user.first_name} {buyer_user.last_name}",
                        order_reference=order.order_number,
                        item_description="Agricultural products"
                    )
                    
                    # Update order with logistics info
                    if logistics_result.get("tracking_number"):
                        order.logistics_tracking_number = logistics_result.get("tracking_number")
                        order.logistics_order_id = logistics_result.get("order_id")
                        order.logistics_partner = logistics_result.get("provider", "kwik")
                        order.status = OrderStatus.IN_TRANSIT
                except Exception as e:
                    # Log error but don't fail the order update
                    order.farmer_notes = (order.farmer_notes or "") + f"\nLogistics error: {str(e)}"
    
    elif status_update.status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()
        
        # Update farmer wallet balance if payment is confirmed
        if order.payment_status == PaymentStatus.PAID:
            # Calculate farmer earnings (subtotal - commission)
            farmer_earnings = order.subtotal - order.commission
            
            # Update farmer wallet
            farmer = db.query(User).filter(User.id == order.farmer_id).first()
            if farmer:
                farmer.wallet_balance += farmer_earnings
    
    elif status_update.status == OrderStatus.REJECTED:
        # Refund if payment was made
        if order.payment_status == PaymentStatus.PAID:
            # Trigger refund process
            # Update order payment status to refunded
            order.payment_status = PaymentStatus.REFUNDED
            
            # Create refund transaction
            from app.models.payment import PaymentTransaction, TransactionType, TransactionStatus
            refund_transaction = PaymentTransaction(
                order_id=order.id,
                user_id=order.buyer_id,
                transaction_type=TransactionType.REFUND,
                amount=order.total_amount,
                status=TransactionStatus.PENDING,
                gateway=order.payment_gateway or "paystack",
                description=f"Refund for order {order.order_number}"
            )
            db.add(refund_transaction)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.put("/profile", response_model=UserResponse)
async def update_farmer_profile(
    profile_data: FarmerProfileUpdate,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Update farmer profile information"""
    update_data = profile_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/withdrawals", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Request withdrawal of earnings"""
    from app.core.config.settings import settings
    
    if withdrawal_data.amount < settings.MIN_WITHDRAWAL_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal amount is {settings.MIN_WITHDRAWAL_AMOUNT}"
        )
    
    if withdrawal_data.amount > current_user.wallet_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient wallet balance"
        )
    
    # Create withdrawal request
    withdrawal = Withdrawal(
        farmer_id=current_user.id,
        amount=withdrawal_data.amount,
        bank_account_number=withdrawal_data.bank_account_number,
        bank_name=withdrawal_data.bank_name,
        account_name=withdrawal_data.account_name,
        status=TransactionStatus.PENDING
    )
    
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    
    return withdrawal


@router.get("/withdrawals", response_model=List[WithdrawalResponse])
async def get_withdrawals(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Get withdrawal history"""
    withdrawals = db.query(Withdrawal).filter(
        Withdrawal.farmer_id == current_user.id
    ).order_by(Withdrawal.created_at.desc()).offset(skip).limit(limit).all()
    
    return withdrawals

