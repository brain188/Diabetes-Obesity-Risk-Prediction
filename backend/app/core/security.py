"""
Security utilities for authentication and data protection.
Handles password hashing, JWT tokens, and security-related functions.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ========== Password Functions ==========

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ========== JWT Token Functions ==========

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    # Encode and sign the token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Created access token for user: {data.get('sub', 'unknown')}")
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded claims if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


def verify_token_expiration(payload: Dict[str, Any]) -> bool:
    """
    Check if a token's expiration time has passed.
    
    Args:
        payload: Decoded JWT payload
        
    Returns:
        True if token is still valid, False if expired
    """
    exp = payload.get("exp")
    if exp is None:
        return False
    
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    return exp_datetime > datetime.now(timezone.utc)


def create_password_reset_token(email: str) -> str:
    """
    Create a short-lived token for password reset.
    
    Args:
        email: User's email address
        
    Returns:
        Encoded password reset token
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "type": "password_reset",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and extract the email.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != "password_reset":
            logger.warning("Invalid password reset token type")
            return None
        
        # Check expiration
        if not verify_token_expiration(payload):
            logger.warning("Password reset token expired")
            return None
        
        return payload.get("sub")
    except JWTError as e:
        logger.warning(f"Password reset token decode error: {str(e)}")
        return None


# ========== Security Exceptions ==========

def raise_unauthorized(detail: str = "Could not validate credentials") -> None:
    """Raise HTTP 401 Unauthorized exception."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_forbidden(detail: str = "Not enough permissions") -> None:
    """Raise HTTP 403 Forbidden exception."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )