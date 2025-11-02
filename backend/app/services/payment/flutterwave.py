import httpx
from typing import Optional, Dict, Any
from app.core.config.settings import settings


async def initialize_payment(
    email: str,
    amount: float,
    reference: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Initialize payment with Flutterwave"""
    url = "https://api.flutterwave.com/v3/payments"
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "tx_ref": reference,
        "amount": amount,
        "currency": "NGN",
        "redirect_url": f"{settings.FLUTTERWAVE_CALLBACK_URL or 'http://localhost:8000/api/v1/payments/callback'}/flutterwave",
        "payment_options": "card,banktransfer,ussd",
        "customer": {
            "email": email
        },
        "meta": metadata or {}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def verify_payment(reference: str) -> Dict[str, Any]:
    """Verify payment status with Flutterwave"""
    url = f"https://api.flutterwave.com/v3/transactions/{reference}/verify"
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


async def create_transfer_recipient(
    account_number: str,
    bank_code: str,
    account_name: str
) -> Dict[str, Any]:
    """Create transfer recipient for withdrawals"""
    url = "https://api.flutterwave.com/v3/beneficiaries"
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "account_bank": bank_code,
        "account_number": account_number,
        "beneficiary_name": account_name,
        "currency": "NGN"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def initiate_transfer(
    account_number: str,
    bank_code: str,
    amount: float,
    reference: str,
    narration: str = "Farmer withdrawal"
) -> Dict[str, Any]:
    """Initiate transfer to farmer bank account"""
    url = "https://api.flutterwave.com/v3/transfers"
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": amount,
        "narration": narration,
        "currency": "NGN",
        "reference": reference,
        "callback_url": f"{settings.FLUTTERWAVE_CALLBACK_URL or 'http://localhost:8000/api/v1/payments/callback'}/flutterwave/transfer"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

