"""
FastAPI dependency injection utilities.
Provides reusable dependencies for routes.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings, get_settings
from app.core.database import get_db_session
from app.core.security import decode_access_token, verify_token_expiration, raise_unauthorized
from app.core.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Security scheme for Bearer tokens
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> str:
    """
    Extract and validate the current user ID from the JWT token.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        
    Returns:
        User ID (email) from the token
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not credentials:
        logger.warning("No authorization token provided")
        raise_unauthorized("Not authenticated")
    
    token = credentials.credentials
    
    # Decode and validate token
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Invalid token format or signature")
        raise_unauthorized("Invalid authentication token")
    
    # Check expiration
    if not verify_token_expiration(payload):
        logger.warning("Token has expired")
        raise_unauthorized("Token has expired")
    
    # Extract user ID (stored as 'sub' claim)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing subject claim")
        raise_unauthorized("Invalid token payload")
    
    # Store token info in request state for logging
    request.state.user_id = user_id
    request.state.token_exp = payload.get("exp")
    
    logger.debug(f"Authenticated user: {user_id}")
    return user_id


async def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[str]:
    """
    Extract user ID if token is provided and valid, otherwise return None.
    Used for optional authentication endpoints.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials (optional)
        
    Returns:
        User ID if valid token provided, None otherwise
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None or not verify_token_expiration(payload):
        return None
    
    return payload.get("sub")


async def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles proxy headers for accurate IP detection.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded headers (when behind a proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (client)
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-IP", request.client.host if request.client else "unknown")
    
    return client_ip or "unknown"


async def get_request_metadata(request: Request) -> Dict[str, Any]:
    """
    Extract request metadata for logging and auditing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with request metadata
    """
    return {
        "request_id": request.headers.get("X-Request-ID", "-"),
        "client_ip": await get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "-"),
        "method": request.method,
        "path": request.url.path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Convenience dependency for settings
ConfigDep = Depends(get_settings)
DbSessionDep = Depends(get_db_session)
CurrentUserDep = Depends(get_current_user_id)
OptionalUserDep = Depends(get_optional_user_id)
ClientIpDep = Depends(get_client_ip)