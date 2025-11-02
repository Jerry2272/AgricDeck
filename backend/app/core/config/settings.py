from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/agricdeck"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # Payment Gateways
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    FLUTTERWAVE_SECRET_KEY: str = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
    FLUTTERWAVE_PUBLIC_KEY: str = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
    
    # Logistics APIs
    KWIK_API_KEY: str = os.getenv("KWIK_API_KEY", "")
    KWIK_API_URL: str = os.getenv("KWIK_API_URL", "https://api.kwik.delivery/v1")
    
    # Callback URLs
    FLUTTERWAVE_CALLBACK_URL: str = os.getenv("FLUTTERWAVE_CALLBACK_URL", "http://localhost:8000/api/v1/payments")
    
    # Platform Settings
    COMMISSION_PERCENTAGE: float = float(os.getenv("COMMISSION_PERCENTAGE", "5.0"))
    MIN_WITHDRAWAL_AMOUNT: float = float(os.getenv("MIN_WITHDRAWAL_AMOUNT", "1000.0"))
    
    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "media")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    class Config:
        env_file = ".env"

settings = Settings()
