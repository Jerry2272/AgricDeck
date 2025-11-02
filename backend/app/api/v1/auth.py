from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config.db import get_db
from app.core.auth.jwt import create_access_token, get_current_active_user
from app.core.auth.password import verify_password, get_password_hash
from app.schemas.user import UserCreate, Token, UserResponse, FarmerOnboarding
from app.models.user import User, UserRole, VerificationStatus
from app.schemas.payment import EarningsResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists
    if db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        verification_status=VerificationStatus.PENDING
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/farmer-onboarding", response_model=UserResponse)
async def farmer_onboarding(
    farmer_data: FarmerOnboarding,
    db: Session = Depends(get_db)
):
    """Complete farmer onboarding with verification details"""
    # Check if user exists
    user = db.query(User).filter(
        (User.email == farmer_data.email) | (User.phone == farmer_data.phone)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first."
        )
    
    if user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a farmer"
        )
    
    # Update farmer details
    user.farm_name = farmer_data.farm_name
    user.farm_address = farmer_data.farm_address
    user.farm_location_state = farmer_data.farm_location_state
    user.farm_location_city = farmer_data.farm_location_city
    user.farm_location_coordinates = farmer_data.farm_location_coordinates
    user.bank_account_number = farmer_data.bank_account_number
    user.bank_name = farmer_data.bank_name
    user.account_name = farmer_data.account_name
    user.verification_document_url = farmer_data.verification_document_url
    user.verification_status = VerificationStatus.PENDING
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.get("/earnings", response_model=EarningsResponse)
async def get_earnings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get farmer earnings summary"""
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can view earnings"
        )
    
    from app.models.order import Order, OrderStatus
    from app.models.payment import Withdrawal, TransactionStatus
    
    # Get total sales
    total_orders = db.query(Order).filter(
        Order.farmer_id == current_user.id,
        Order.status == OrderStatus.DELIVERED
    ).count()
    
    # Calculate total earnings from delivered orders
    delivered_orders = db.query(Order).filter(
        Order.farmer_id == current_user.id,
        Order.status == OrderStatus.DELIVERED
    ).all()
    
    total_earnings = sum(order.subtotal - order.commission for order in delivered_orders)
    
    # Get pending withdrawals
    pending_withdrawals = db.query(Withdrawal).filter(
        Withdrawal.farmer_id == current_user.id,
        Withdrawal.status == TransactionStatus.PENDING
    ).all()
    
    pending_amount = sum(w.amount for w in pending_withdrawals)
    
    return EarningsResponse(
        total_earnings=total_earnings,
        wallet_balance=current_user.wallet_balance,
        pending_withdrawals=pending_amount,
        total_sales=total_orders,
        total_orders=total_orders
    )
