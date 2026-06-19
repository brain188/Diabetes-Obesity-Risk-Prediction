"""
FastAPI dependency injection utilities.
Provides reusable dependencies for routes.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings, get_settings
from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError, InvalidTokenError, InactiveUserError
from app.core.security import decode_token, verify_token_expiration
from app.core.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Security scheme for Bearer tokens
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> str:
    """
    Extract and validate the current user ID from the JWT access token.

    Validates:
        - Token is present
        - Token signature is valid and not expired (JWTError raised otherwise)
        - Token type is "access" (rejects refresh tokens used as access tokens)
        - "sub" or "worker_id" claim is present

    Args:
        request     : FastAPI request object
        credentials : Bearer token credentials

    Returns:
        worker_id (UUID string) from the token's "sub" claim

    Raises:
        AuthenticationError : If token is missing
        InvalidTokenError   : If token is invalid, expired, or wrong type
    """
    if not credentials:
        logger.warning("No authorization token provided")
        raise AuthenticationError("Not authenticated. Provide a Bearer token.")

    token = credentials.credentials

    # Decode and validate — raises JWTError on expiry / bad signature
    try:
        payload = decode_token(token)
    except JWTError as exc:
        logger.warning("Token decode failed: %s", exc)
        raise InvalidTokenError(f"Invalid authentication token: {exc}")

    # decode_token returns None when token_type param is passed and mismatches,
    # but here we call it without token_type so None means something unexpected
    if payload is None:
        logger.warning("Token decode returned None unexpectedly")
        raise InvalidTokenError("Invalid authentication token.")

    # Reject refresh tokens used as access tokens
    if payload.get("type") != "access":
        logger.warning("Wrong token type: %s", payload.get("type"))
        raise InvalidTokenError(
            "Invalid token type. Use an access token, not a refresh token."
        )

    # Check expiration explicitly (belt-and-suspenders — jose already checks this)
    if not verify_token_expiration(payload):
        logger.warning("Token has expired")
        raise InvalidTokenError("Token has expired.")

    # Extract worker_id — stored in "sub"; "worker_id" is a redundant alias
    worker_id: Optional[str] = payload.get("sub") or payload.get("worker_id")
    if not worker_id:
        logger.warning("Token missing subject claim")
        raise InvalidTokenError("Invalid token payload: missing subject.")

    # Store in request state for downstream logging middleware
    request.state.user_id   = worker_id
    request.state.token_exp = payload.get("exp")

    logger.debug("Authenticated user: %s", worker_id)
    return worker_id


async def get_current_active_worker(
    worker_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Verify the authenticated worker exists in the DB and is still active.

    Use this dependency when a route needs the full ORM object rather than
    just the worker_id string.

    Args:
        worker_id : Resolved by get_current_user_id
        db        : Async database session

    Returns:
        HealthcareWorker ORM instance

    Raises:
        InvalidTokenError  : If the worker no longer exists in the DB
        InactiveUserError  : If the worker's account has been deactivated
    """
    from app.models.healthcare_worker import HealthcareWorker
    from sqlalchemy import select

    result = await db.execute(
        select(HealthcareWorker).where(HealthcareWorker.worker_id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise InvalidTokenError("Worker account no longer exists.")
    if not worker.is_active:
        raise InactiveUserError()

    return worker


async def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[str]:
    """
    Extract user ID if a valid token is provided, otherwise return None.
    Used for endpoints that support both authenticated and anonymous access.

    Args:
        request     : FastAPI request object
        credentials : Bearer token credentials (optional)

    Returns:
        worker_id string if a valid access token is provided, None otherwise.
        Never raises — silently returns None on any token problem.
    """
    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None

    if payload is None or not verify_token_expiration(payload):
        return None

    if payload.get("type") != "access":
        return None

    return payload.get("sub") or payload.get("worker_id")


async def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles proxy headers (X-Forwarded-For, X-Real-IP) for accurate detection
    when the app runs behind a reverse proxy (nginx, load balancer).

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string, or "unknown" if not determinable
    """
    # X-Forwarded-For may contain a comma-separated list; take the first (client)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


async def get_request_metadata(request: Request) -> Dict[str, Any]:
    """
    Extract request metadata for logging and audit trail.

    Collects request_id, client IP, user agent, HTTP method, path,
    and timestamp so audit log entries have full context.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with request metadata
    """
    return {
        "request_id": request.headers.get("X-Request-ID", "-"),
        "client_ip" : await get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "-"),
        "method"    : request.method,
        "path"      : str(request.url.path),
        "timestamp" : datetime.now(timezone.utc).isoformat(),
    }


def get_model_loader(request: Request):
    """
    Retrieve the ML ModelLoader singleton from app.state.

    The loader is attached in main.py's lifespan:
        app.state.model_loader = model_loader
        model_loader.load_all()

    Inject into services that need ML predictions:
        model_loader = Depends(get_model_loader)

    Raises:
        ModelNotLoadedError : If load_all() was never called (startup failure)
    """
    from app.ml.model_loader import ModelLoader
    from app.core.exceptions import ModelNotLoadedError

    loader: ModelLoader = request.app.state.model_loader
    if not loader.is_loaded:
        raise ModelNotLoadedError()
    return loader


# ── Convenience dependency aliases ────────────────────────────────────────────
# Use these in route function signatures for brevity:
#   async def my_route(settings = ConfigDep, db = DbSessionDep, ...):

ConfigDep       = Depends(get_settings)
DbSessionDep    = Depends(get_db_session)
CurrentUserDep  = Depends(get_current_user_id)
OptionalUserDep = Depends(get_optional_user_id)
ClientIpDep     = Depends(get_client_ip)