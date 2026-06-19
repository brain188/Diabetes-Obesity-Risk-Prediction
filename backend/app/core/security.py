"""
JWT token creation/verification and bcrypt password hashing.
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# Access token

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Accepts data: dict so existing call sites (auth_service, conftest) work.
    The "sub" claim must be set by the caller.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp" : expire,
        "iat" : datetime.now(UTC),
        "type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Refresh token ─────────────────────────────────────────────────────────────

def create_refresh_token(data: Dict[str, Any]) -> tuple[str, str, datetime]:
    """
    Create a refresh token.

    Returns (encoded_jwt, sha256_hash, expires_at).
    The hash is stored in the DB; the raw JWT is sent to the client.
    """
    to_encode = data.copy()
    expire    = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp" : expire,
        "iat" : datetime.now(UTC),
        "type": "refresh",
        "jti" : secrets.token_urlsafe(16),
    })
    encoded    = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    token_hash = hashlib.sha256(encoded.encode()).hexdigest()
    return encoded, token_hash, expire


# ── Token decoding ────────────────────────────────────────────────────────────

def decode_token(token: str, token_type: Optional[str] = None) -> dict:
    """
    Decode and validate a JWT token.

    Parameters
    ----------
    token      : encoded JWT string
    token_type : optional "access" or "refresh" — validates the type claim

    Returns the decoded payload dict.
    Returns None (does not raise) when token_type is provided and mismatches,
    so auth_service.refresh_token() can handle it gracefully.
    Raises JWTError for expired / tampered tokens.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    if token_type and payload.get("type") != token_type:
        logger.warning(
            "Token type mismatch: expected %s, got %s",
            token_type, payload.get("type"),
        )
        return None   # type: ignore[return-value]
    return payload


def extract_subject(token: str) -> Optional[str]:
    """
    Safely extract the subject from a token.
    Returns None if the token is invalid — never raises.
    """
    try:
        return decode_token(token).get("sub")
    except JWTError:
        return None


# ── Password reset helpers ────────────────────────────────────────────────────

def create_password_reset_token(email: str) -> str:
    """Create a 30-minute JWT for password reset."""
    expire = datetime.now(UTC) + timedelta(
        minutes=getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 30)
    )
    payload = {
        "sub" : email,
        "type": "password_reset",
        "exp" : expire,
        "iat" : datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email, or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def verify_token_expiration(payload: Dict[str, Any]) -> bool:
    """Return True if the token has not yet expired."""
    exp = payload.get("exp")
    if exp is None:
        return False
    return datetime.fromtimestamp(exp, tz=UTC) > datetime.now(UTC)


# ── Security Exceptions ──────────────────────────────────────────────────────

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