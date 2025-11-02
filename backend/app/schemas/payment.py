from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.payment import TransactionType, TransactionStatus


class PaymentInitiate(BaseModel):
    order_id: int
    payment_method: str  # card, bank_transfer, ussd, wallet
    gateway: str = "paystack"  # paystack or flutterwave


class PaymentVerification(BaseModel):
    reference: str
    gateway: str = "paystack"


class PaymentResponse(BaseModel):
    id: int
    order_id: Optional[int] = None
    transaction_type: TransactionType
    amount: float
    status: TransactionStatus
    gateway: str
    gateway_reference: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WithdrawalRequest(BaseModel):
    amount: float
    bank_account_number: str
    bank_name: str
    account_name: str


class WithdrawalResponse(BaseModel):
    id: int
    farmer_id: int
    amount: float
    status: TransactionStatus
    bank_account_number: str
    bank_name: str
    account_name: str
    gateway_reference: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EarningsResponse(BaseModel):
    total_earnings: float
    wallet_balance: float
    pending_withdrawals: float
    total_sales: int
    total_orders: int

