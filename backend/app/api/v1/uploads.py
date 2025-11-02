from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from app.core.config.db import get_db
from app.core.config.settings import settings
from app.core.auth.jwt import get_current_active_user, require_role
from app.models.user import User, UserRole
from typing import List

router = APIRouter(prefix="/uploads", tags=["Uploads"])

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create subdirectories
PRODUCT_IMAGES_DIR = UPLOAD_DIR / "products"
PROFILE_IMAGES_DIR = UPLOAD_DIR / "profiles"
DOCUMENTS_DIR = UPLOAD_DIR / "documents"

for directory in [PRODUCT_IMAGES_DIR, PROFILE_IMAGES_DIR, DOCUMENTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}


def validate_file(file: UploadFile, allowed_extensions: set, max_size: int = None):
    """Validate uploaded file"""
    # Check extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # File size will be checked by FastAPI automatically based on request size limit
    return file_extension


@router.post("/product-images", response_model=List[str])
async def upload_product_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload product images"""
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed"
        )
    
    uploaded_urls = []
    
    for file in files:
        # Validate file
        extension = validate_file(file, ALLOWED_IMAGE_EXTENSIONS)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}{extension}"
        file_path = PRODUCT_IMAGES_DIR / filename
        
        # Save file
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate URL (adjust based on your server configuration)
        file_url = f"/api/v1/uploads/files/product-images/{filename}"
        uploaded_urls.append(file_url)
    
    return uploaded_urls


@router.post("/profile-image", response_model=str)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    # Validate file
    extension = validate_file(file, ALLOWED_IMAGE_EXTENSIONS)
    
    # Delete old profile image if exists
    if current_user.profile_image_url:
        old_file_path = Path(settings.UPLOAD_DIR) / current_user.profile_image_url.replace("/api/v1/uploads/files/", "")
        if old_file_path.exists():
            old_file_path.unlink()
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{extension}"
    file_path = PROFILE_IMAGES_DIR / filename
    
    # Save file
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update user profile image URL
    file_url = f"/api/v1/uploads/files/profile-images/{filename}"
    current_user.profile_image_url = file_url
    
    db.commit()
    db.refresh(current_user)
    
    return file_url


@router.post("/verification-document", response_model=str)
async def upload_verification_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.FARMER])),
    db: Session = Depends(get_db)
):
    """Upload verification document for farmer KYC"""
    # Validate file
    extension = validate_file(file, ALLOWED_DOCUMENT_EXTENSIONS)
    
    # Delete old document if exists
    if current_user.verification_document_url:
        old_file_path = Path(settings.UPLOAD_DIR) / current_user.verification_document_url.replace("/api/v1/uploads/files/", "")
        if old_file_path.exists():
            old_file_path.unlink()
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{extension}"
    file_path = DOCUMENTS_DIR / filename
    
    # Save file
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE * 2:  # Documents can be larger
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE * 2} bytes"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update user verification document URL
    file_url = f"/api/v1/uploads/files/documents/{filename}"
    current_user.verification_document_url = file_url
    
    db.commit()
    db.refresh(current_user)
    
    return file_url


@router.get("/files/{category}/{filename}")
async def get_file(
    category: str,
    filename: str,
    db: Session = Depends(get_db)
):
    """Serve uploaded files"""
    if category == "product-images":
        file_path = PRODUCT_IMAGES_DIR / filename
    elif category == "profile-images":
        file_path = PROFILE_IMAGES_DIR / filename
    elif category == "documents":
        file_path = DOCUMENTS_DIR / filename
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category"
        )
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path)

