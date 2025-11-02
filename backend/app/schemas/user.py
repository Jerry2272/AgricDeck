from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, VerificationStatus


class UserBase(BaseModel):
    email: EmailStr
    phone: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.BUYER
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class FarmerOnboarding(UserBase):
    farm_name: str
    farm_address: str
    farm_location_state: str
    farm_location_city: str
    farm_location_coordinates: Optional[str] = None
    bank_account_number: str
    bank_name: str
    account_name: str
    verification_document_url: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None


class FarmerProfileUpdate(BaseModel):
    farm_name: Optional[str] = None
    farm_address: Optional[str] = None
    farm_location_state: Optional[str] = None
    farm_location_city: Optional[str] = None
    farm_location_coordinates: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    phone: str
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    verification_status: VerificationStatus
    wallet_balance: float
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location_state: Optional[str] = None
    farm_location_city: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FarmerProfileResponse(UserResponse):
    farm_address: Optional[str] = None
    farm_location_coordinates: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None

