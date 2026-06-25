"""
Authentication business logic.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    verify_password_reset_token,
    verify_token_expiration,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.healthcare_worker_repository import HealthcareWorkerRepository

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication-related business logic.
    Handles user registration, login, token management, and password operations.
    """

    def __init__(self, session) -> None:
        """
        Initialize the auth service with a database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session      = session
        self.worker_repo  = HealthcareWorkerRepository(session)  # Repository for worker/user operations
        self.audit_repo   = AuditLogRepository(session)          # Repository for audit logging

    # ----- Register ---------------------------------------------------------------

    async def register(
        self,
        full_name: str,
        email: str,
        password: str,
        clinic_name: Optional[str] = None,
        role: str = "healthcare_worker",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Register a new healthcare worker account.
        
        Args:
            full_name: Worker's full name
            email: Worker's email address (must be unique)
            password: Plain text password (will be hashed)
            clinic_name: Optional clinic/facility name
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            Dictionary with worker information including is_active flag
            
        Raises:
            DuplicateError: If email already exists in the system
        """
        # Create the worker account - password hashing happens inside the repository
        worker = await self.worker_repo.create_worker(
            full_name   = full_name,
            email       = email,
            password    = password,
            clinic_name = clinic_name,
            role        = role,
        )

        # Log the registration event for audit trail
        await self.audit_repo.log_event(
            event_type = "REGISTER",
            action     = f"New user registered: {email}",
            worker_id  = worker.worker_id,
            ip_address = ip_address,
            user_agent = user_agent,
            status     = "SUCCESS",
        )

        logger.info("User registered: %s", email)

        # Return data matching UserRegisterResponse schema
        return {
            "worker_id"  : worker.worker_id,
            "full_name"  : worker.full_name,
            "email"      : worker.email,
            "clinic_name": worker.clinic_name,
            "role"       : worker.role,
            "is_active"  : worker.is_active,
            "created_at" : worker.created_at,
        }

    # ------- Login -------------------------------------------------------------------

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Authenticate a user and generate access/refresh tokens.
        
        Implements refresh token rotation: each login creates a new refresh token
        and revokes any existing ones.
        
        Args:
            email: User's email address
            password: User's password
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
            request_id: Request correlation ID for tracing
            
        Returns:
            Dictionary with access_token, refresh_token, and user information
            
        Raises:
            AuthenticationError: If credentials are invalid or account is inactive
        """
        try:
            # Authenticate the user - validates credentials and checks account status
            worker = await self.worker_repo.authenticate(email, password)

            # ----- Create Access Token ---------------------------------------------
            # Access token is short-lived
            access_token = create_access_token(
                data={
                    "sub"      : worker.worker_id,
                    "worker_id": worker.worker_id,
                    "email"    : worker.email,
                },
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            # ------- Create Refresh Token (with rotation) --------------------------------
            # Revoke any existing refresh token to prevent token reuse attacks
            await self.worker_repo.revoke_refresh_token(worker.worker_id)
            
            # Create new refresh token (longer-lived, typically 7 days)
            refresh_token, token_hash, expires_at = create_refresh_token(
                data={
                    "sub"      : worker.worker_id,
                    "worker_id": worker.worker_id,
                    "email"    : worker.email,
                }
            )
            
            # Store the hashed refresh token for validation during refresh
            await self.worker_repo.store_refresh_token(
                worker_id  = worker.worker_id,
                token_hash = token_hash,
                expires_at = expires_at,
            )

            # ---- Audit Logging --------------------------------------------------
            # Log successful login - signature: email, success, worker_id
            await self.audit_repo.log_login(
                email      = email,
                success    = True,
                ip_address = ip_address,
                user_agent = user_agent,
                request_id = request_id,
                worker_id  = worker.worker_id,
            )

            logger.info("User logged in: %s", email)

            # Return token response with user information
            return {
                "access_token"      : access_token,
                "refresh_token"     : refresh_token,
                "token_type"        : "bearer",
                "expires_in"        : settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                "user": {
                    "worker_id"    : worker.worker_id,
                    "full_name"    : worker.full_name,
                    "email"        : worker.email,
                    "clinic_name"  : worker.clinic_name,
                    "role"         : getattr(worker, "role", "healthcare_worker"),
                    "is_active"    : worker.is_active,
                    "last_login_at": getattr(worker, "last_login_at", None),
                    "created_at"   : worker.created_at,
                },
            }

        except AuthenticationError:
            # Log failed login attempt for security monitoring
            await self.audit_repo.log_login(
                email      = email,
                success    = False,
                ip_address = ip_address,
                user_agent = user_agent,
                request_id = request_id,
            )
            logger.warning("Failed login: %s", email)
            raise  # Re-raise the exception to be handled by the endpoint

    # -------- Refresh token -------------------------------------------------------

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refresh an access token using a valid refresh token.
        
        Implements refresh token rotation:
        1. Validate the refresh token
        2. Issue a new access token
        3. Issue a new refresh token (rotation)
        4. Revoke the old refresh token
        
        Security features:
        - Refresh token rotation prevents replay attacks
        - Token theft detection (using validated token)
        
        Args:
            refresh_token: The refresh token to use
            ip_address: Client IP for audit logging
            
        Returns:
            Dictionary with new access_token and refresh_token
            
        Raises:
            AuthenticationError: If refresh token is invalid, expired, or revoked
        """
        # --------- Decode and validate refresh token -------------------------------------
        # decode_token returns None on type mismatch, raises JWTError on expiry
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except Exception:
            raise AuthenticationError("Invalid refresh token.")

        if not payload:
            raise AuthenticationError("Invalid refresh token type.")

        # Check if the token has expired
        if not verify_token_expiration(payload):
            raise AuthenticationError("Refresh token has expired.")

        # Extract worker_id from payload (supports both 'sub' and 'worker_id' claims)
        worker_id = payload.get("sub") or payload.get("worker_id")
        if not worker_id:
            raise AuthenticationError("Invalid refresh token payload.")

        # ----- Validate against stored hash -------------------------------------------
        # Verify that the token matches the stored hash in database
        is_valid = await self.worker_repo.validate_refresh_token(worker_id, refresh_token)
        if not is_valid:
            # Token might be compromised or already used - revoke all tokens as security measure
            await self.worker_repo.revoke_refresh_token(worker_id)
            raise AuthenticationError("Refresh token is invalid or already used.")

        # ------- Get user and verify status ----------------------------------------------
        worker = await self.worker_repo.get_by_id(worker_id, id_column="worker_id")
        if not worker or not worker.is_active:
            raise AuthenticationError("User not found or inactive.")

        # ------- Rotate tokens --------------------------------------------------
        # Revoke the old refresh token (already validated)
        await self.worker_repo.revoke_refresh_token(worker_id)

        # Create new access token
        new_access = create_access_token(
            data={"sub": worker.worker_id, "worker_id": worker.worker_id, "email": worker.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        # Create new refresh token
        new_refresh, token_hash, expires_at = create_refresh_token(
            data={"sub": worker.worker_id, "worker_id": worker.worker_id, "email": worker.email}
        )
        
        # Store the new refresh token hash
        await self.worker_repo.store_refresh_token(
            worker_id=worker.worker_id, token_hash=token_hash, expires_at=expires_at
        )

        # ── Log the refresh event ────────────────────────────────────────────
        await self.audit_repo.log_event(
            event_type = "TOKEN_REFRESHED",
            action     = f"Token refreshed for worker {worker.worker_id}",
            worker_id  = worker.worker_id,
            ip_address = ip_address,
            status     = "SUCCESS",
        )

        # Return new token pair
        return {
            "access_token"      : new_access,
            "refresh_token"     : new_refresh,
            "token_type"        : "bearer",
            "expires_in"        : settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        }

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(
        self,
        worker_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Log out a user by revoking their refresh token.
        
        Args:
            worker_id: Worker identifier
            ip_address: Client IP for audit logging
            request_id: Request correlation ID for tracing
        """
        # Revoke the refresh token to prevent further token refresh
        await self.worker_repo.revoke_refresh_token(worker_id)
        
        # Log the logout event
        await self.audit_repo.log_logout(
            worker_id  = worker_id,
            ip_address = ip_address,
            request_id = request_id,
        )
        logger.info("Worker logged out: %s", worker_id)

    # ── Password management ───────────────────────────────────────────────────

    async def request_password_reset(
        self, email: str, ip_address: Optional[str] = None
    ) -> None:
        """
        Request a password reset for a user.
        
        Creates a reset token and stores it in the database.
        Silent on failure to prevent email enumeration attacks.
        
        Args:
            email: User's email address
            ip_address: Client IP for audit logging
        """
        worker = await self.worker_repo.get_by_email(email)
        if not worker:
            return   # Silent — never reveal if email exists for security reasons

        # Create a short-lived password reset token
        token   = create_password_reset_token(email)
        
        # Store token in database with expiration
        success = await self.worker_repo.set_password_reset_token(
            email           = email,
            token           = token,
            expires_minutes = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 30),
        )
        
        # Log the request if successful
        if success:
            await self.audit_repo.log_event(
                event_type = "PASSWORD_RESET_REQUEST",
                action     = f"Password reset requested: {email}",
                worker_id  = worker.worker_id,
                ip_address = ip_address,
                status     = "SUCCESS",
            )

    async def reset_password(
        self, token: str, new_password: str, ip_address: Optional[str] = None
    ) -> bool:
        """
        Reset a user's password using a valid reset token.
        
        Args:
            token: Password reset token from email
            new_password: New password to set
            ip_address: Client IP for audit logging
            
        Returns:
            True if password was reset successfully
            
        Raises:
            AuthenticationError: If token is invalid, expired, or user not found
        """
        # Verify the reset token and extract email
        email = verify_password_reset_token(token)
        if not email:
            raise AuthenticationError("Invalid or expired reset token.")

        # Get the user by email
        worker = await self.worker_repo.get_by_email(email)
        if not worker:
            raise AuthenticationError("User not found.")

        # Validate that the token matches the stored one
        if worker.password_reset_token != token:
            raise AuthenticationError("Invalid reset token.")

        # Check if the token has expired
        if worker.password_reset_expires and worker.password_reset_expires < datetime.now(UTC):
            raise AuthenticationError("Reset token has expired.")

        # Reset the password (this clears the reset token)
        success = await self.worker_repo.reset_password(worker.worker_id, new_password)
        
        # Log the successful reset
        if success:
            await self.audit_repo.log_event(
                event_type = "PASSWORD_RESET",
                action     = f"Password reset: {email}",
                worker_id  = worker.worker_id,
                ip_address = ip_address,
                status     = "SUCCESS",
            )
        return success

    async def change_password(
        self,
        worker_id: str,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Change a user's password (requires current password verification).
        
        Args:
            worker_id: Worker identifier
            current_password: Current password for verification
            new_password: New password to set
            ip_address: Client IP for audit logging
            
        Returns:
            True if password was changed successfully
            
        Raises:
            AuthenticationError: If current password is incorrect
            NotFoundError: If user not found
        """
        # Attempt to change password (repository handles verification)
        success = await self.worker_repo.change_password(
            worker_id        = worker_id,
            current_password = current_password,
            new_password     = new_password,
        )
        
        # Log the change if successful
        if success:
            await self.audit_repo.log_event(
                event_type = "PASSWORD_CHANGE",
                action     = "Password changed",
                worker_id  = worker_id,
                ip_address = ip_address,
                status     = "SUCCESS",
            )
        return success

    async def list_users(self) -> list[dict]:
        """Return all registered users (healthcare workers and admins)."""
        workers = await self.worker_repo.list_workers()
        return [
            {
                "worker_id"    : w.worker_id,
                "full_name"    : w.full_name,
                "email"        : w.email,
                "clinic_name"  : w.clinic_name,
                "role"         : getattr(w, "role", "healthcare_worker"),
                "is_active"    : w.is_active,
                "last_login_at": getattr(w, "last_login_at", None),
                "created_at"   : w.created_at,
            }
            for w in workers
        ]

    async def get_user_profile(self, worker_id: str) -> dict:
        """
        Get user profile information.
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Dictionary with user profile data
            
        Raises:
            NotFoundError: If user not found
        """
        # Get worker by ID
        worker = await self.worker_repo.get_by_id(worker_id, id_column="worker_id")
        if not worker:
            raise NotFoundError("HealthcareWorker", worker_id)
        
        # Return profile data
        return {
            "worker_id"    : worker.worker_id,
            "full_name"    : worker.full_name,
            "email"        : worker.email,
            "clinic_name"  : worker.clinic_name,
            "role"         : getattr(worker, "role", "healthcare_worker"),
            "is_active"    : worker.is_active,
            "last_login_at": getattr(worker, "last_login_at", None),
            "created_at"   : worker.created_at,
        }