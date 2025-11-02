from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.config.db import get_db
from app.core.auth.jwt import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import PaymentTransaction, TransactionType, TransactionStatus
from app.schemas.payment import PaymentInitiate, PaymentVerification, PaymentResponse
from app.services.payment import paystack, flutterwave
import uuid
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate", response_model=dict)
async def initiate_payment(
    payment_data: PaymentInitiate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initiate payment for an order"""
    # Get order
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.buyer_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )
    
    # Generate payment reference
    payment_reference = f"AGD-{uuid.uuid4().hex[:12].upper()}"
    
    # Create payment transaction
    payment_transaction = PaymentTransaction(
        order_id=order.id,
        user_id=current_user.id,
        transaction_type=TransactionType.PAYMENT,
        amount=order.total_amount,
        status=TransactionStatus.PENDING,
        gateway=payment_data.gateway,
        gateway_reference=payment_reference,
        payment_method=payment_data.payment_method,
        description=f"Payment for order {order.order_number}"
    )
    
    db.add(payment_transaction)
    db.flush()
    
    # Initialize payment with gateway
    try:
        if payment_data.gateway == "paystack":
            payment_result = await paystack.initialize_payment(
                email=current_user.email,
                amount=order.total_amount,
                reference=payment_reference,
                metadata={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": current_user.id
                }
            )
            authorization_url = payment_result.get("data", {}).get("authorization_url")
            access_code = payment_result.get("data", {}).get("access_code")
        elif payment_data.gateway == "flutterwave":
            payment_result = await flutterwave.initialize_payment(
                email=current_user.email,
                amount=order.total_amount,
                reference=payment_reference,
                metadata={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": current_user.id
                }
            )
            authorization_url = payment_result.get("data", {}).get("link")
            access_code = payment_result.get("data", {}).get("flw_ref")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment gateway"
            )
        
        # Update order with payment reference
        order.payment_reference = payment_reference
        order.payment_gateway = payment_data.gateway
        order.payment_method = payment_data.payment_method
        order.payment_status = PaymentStatus.PROCESSING
        
        payment_transaction.gateway_response = str(payment_result)
        
        db.commit()
        
        return {
            "authorization_url": authorization_url,
            "access_code": access_code,
            "reference": payment_reference,
            "gateway": payment_data.gateway,
            "amount": order.total_amount
        }
    except Exception as e:
        payment_transaction.status = TransactionStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    payment_data: PaymentVerification,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify payment status"""
    # Find payment transaction
    payment_transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.gateway_reference == payment_data.reference,
        PaymentTransaction.user_id == current_user.id
    ).first()
    
    if not payment_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found"
        )
    
    # Verify with gateway
    try:
        if payment_data.gateway == "paystack":
            verification_result = await paystack.verify_payment(payment_data.reference)
            transaction_data = verification_result.get("data", {})
            is_successful = transaction_data.get("status") == "success"
            amount_paid = transaction_data.get("amount", 0) / 100  # Convert from kobo
        elif payment_data.gateway == "flutterwave":
            verification_result = await flutterwave.verify_payment(payment_data.reference)
            transaction_data = verification_result.get("data", {})
            is_successful = transaction_data.get("status") == "successful"
            amount_paid = transaction_data.get("amount", 0)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment gateway"
            )
        
        # Update payment transaction
        payment_transaction.gateway_response = str(verification_result)
        
        if is_successful:
            payment_transaction.status = TransactionStatus.SUCCESS
            payment_transaction.completed_at = datetime.utcnow()
            
            # Update order payment status
            if payment_transaction.order_id:
                order = db.query(Order).filter(Order.id == payment_transaction.order_id).first()
                if order:
                    order.payment_status = PaymentStatus.PAID
                    
                    # Update farmer wallet when order is delivered
                    # (This will be handled when order status changes to delivered)
        else:
            payment_transaction.status = TransactionStatus.FAILED
        
        db.commit()
        db.refresh(payment_transaction)
        
        return payment_transaction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )


@router.post("/webhooks/paystack")
async def paystack_webhook(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook"""
    # Verify webhook signature if needed
    event = request_data.get("event")
    data = request_data.get("data", {})
    
    reference = data.get("reference")
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook data"
        )
    
    # Find payment transaction
    payment_transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.gateway_reference == reference
    ).first()
    
    if not payment_transaction:
        return {"status": "transaction_not_found"}
    
    # Handle event
    if event == "charge.success":
        payment_transaction.status = TransactionStatus.SUCCESS
        payment_transaction.completed_at = datetime.utcnow()
        
        # Update order
        if payment_transaction.order_id:
            order = db.query(Order).filter(Order.id == payment_transaction.order_id).first()
            if order:
                order.payment_status = PaymentStatus.PAID
    
    elif event == "charge.failed":
        payment_transaction.status = TransactionStatus.FAILED
    
    db.commit()
    
    return {"status": "ok"}


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """Handle Flutterwave webhook"""
    event = request_data.get("event")
    data = request_data.get("data", {})
    
    reference = data.get("tx_ref")
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook data"
        )
    
    # Find payment transaction
    payment_transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.gateway_reference == reference
    ).first()
    
    if not payment_transaction:
        return {"status": "transaction_not_found"}
    
    # Handle event
    if event == "charge.completed" and data.get("status") == "successful":
        payment_transaction.status = TransactionStatus.SUCCESS
        payment_transaction.completed_at = datetime.utcnow()
        
        # Update order
        if payment_transaction.order_id:
            order = db.query(Order).filter(Order.id == payment_transaction.order_id).first()
            if order:
                order.payment_status = PaymentStatus.PAID
    
    elif event == "charge.completed" and data.get("status") != "successful":
        payment_transaction.status = TransactionStatus.FAILED
    
    db.commit()
    
    return {"status": "ok"}


@router.get("/transactions", response_model=list[PaymentResponse])
async def get_payment_transactions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment transactions for current user"""
    transactions = db.query(PaymentTransaction).filter(
        PaymentTransaction.user_id == current_user.id
    ).order_by(PaymentTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return transactions

