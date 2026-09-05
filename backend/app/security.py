import os
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, status
from passlib.context import CryptContext
import jwt
from sqlalchemy.orm import Session

from .models import AdminUser


# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ADMIN_JWT_EXPIRY_HOURS = int(os.getenv("ADMIN_JWT_EXPIRY_HOURS", "8"))
QR_TOKEN_SECRET = os.getenv("QR_TOKEN_SECRET", "your-qr-secret-change-in-production")
ALGORITHM = "HS256"

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================================
# Password Hashing & Verification
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, password_hash)


# ============================================================================
# Admin JWT (Bearer Token)
# ============================================================================

def create_admin_token(admin_id: int, username: str) -> str:
    """Create a JWT token for an admin user."""
    payload = {
        "admin_id": admin_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=ADMIN_JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_admin_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises HTTPException if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_admin(token: str, db: Session) -> AdminUser:
    """
    FastAPI dependency to validate admin JWT and return the admin user.
    Usage: def some_endpoint(admin: AdminUser = Depends(get_current_admin)):
    """
    payload = verify_admin_token(token)
    admin_id = payload.get("admin_id")
    
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found"
        )
    
    return admin


# ============================================================================
# QR / Pass Token (HMAC-signed)
# ============================================================================

def create_qr_token(roll_number: str) -> str:
    """
    Create an HMAC-signed token encoding the roll number.
    Format: base64(roll_number + "." + hmac_sha256(secret, roll_number))
    """
    normalized_roll = roll_number.strip().upper()
    
    # Compute HMAC-SHA256
    signature = hmac.new(
        QR_TOKEN_SECRET.encode(),
        normalized_roll.encode(),
        hashlib.sha256
    ).digest()
    
    # Format: roll_number.base64(signature)
    token_payload = f"{normalized_roll}.{base64.b64encode(signature).decode()}"
    
    # Base64 encode the entire token
    token = base64.b64encode(token_payload.encode()).decode()
    return token


def verify_qr_token(token: str) -> str:
    """
    Verify an HMAC-signed token and return the roll_number if valid.
    Raises HTTPException if the token is invalid or tampered.
    """
    try:
        # Decode from base64
        token_payload = base64.b64decode(token.encode()).decode()
        
        # Split into roll_number and signature
        parts = token_payload.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError("Invalid token format")
        
        roll_number, signature_b64 = parts
        
        # Verify signature
        expected_signature = hmac.new(
            QR_TOKEN_SECRET.encode(),
            roll_number.encode(),
            hashlib.sha256
        ).digest()
        
        provided_signature = base64.b64decode(signature_b64.encode())
        
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Signature verification failed")
        
        return roll_number
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or tampered QR token"
        )


# ============================================================================
# Utility: Authenticate Admin (username + password)
# ============================================================================

def authenticate_admin(username: str, password: str, db: Session) -> Optional[AdminUser]:
    """
    Authenticate an admin by username and password.
    Returns the AdminUser if valid, None otherwise.
    """
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    
    if not admin:
        return None
    
    if not verify_password(password, admin.password_hash):
        return None
    
    return admin
