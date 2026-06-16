"""
Authentication business logic.
Handles user registration, login, password management, and token operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.core.exceptions import AuthenticationError, NotFoundError
from app.repositories.healthcare_worker_repository import HealthcareWorkerRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication-related business logic."""
    
    def __init__(self, session):
        """
        Initialize auth service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.worker_repo = HealthcareWorkerRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.audit_service = AuditService(session)
    
    async def register(
        self,
        full_name: str,
        email: str,
        password: str,
        clinic_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """
        Register a new healthcare worker.
        
        Args:
            full_name: Worker's full name
            email: Email address
            password: Plain text password
            clinic_name: Optional clinic name
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with worker information
        """
        # Create worker
        worker = await self.worker_repo.create_worker(
            full_name=full_name,
            email=email,
            password=password,
            clinic_name=clinic_name
        )
        
        # Log registration
        await self.audit_repo.log_event(
            event_type="REGISTER",
            action=f"New user registered: {email}",
            worker_id=worker.worker_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="SUCCESS"
        )
        
        logger.info(f"User registered successfully: {email}")
        
        return {
            "worker_id": worker.worker_id,
            "full_name": worker.full_name,
            "email": worker.email,
            "clinic_name": worker.clinic_name,
            "created_at": worker.created_at
        }
    
    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> dict:
        """
        Authenticate a user and return access token.
        
        Args:
            email: User's email
            password: User's password
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            request_id: Request ID for tracing
            
        Returns:
            Dictionary with access token and user info
        """
        try:
            # Authenticate user
            worker = await self.worker_repo.authenticate(email, password)
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": worker.email, "worker_id": worker.worker_id},
                expires_delta=access_token_expires
            )
            
            # Log successful login
            await self.audit_repo.log_login(
                email=email,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                worker_id=worker.worker_id
            )
            
            logger.info(f"User logged in successfully: {email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "worker_id": worker.worker_id,
                    "full_name": worker.full_name,
                    "email": worker.email,
                    "clinic_name": worker.clinic_name
                }
            }
            
        except AuthenticationError:
            # Log failed login attempt
            await self.audit_repo.log_login(
                email=email,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id
            )
            logger.warning(f"Failed login attempt for: {email}")
            raise
    
    async def logout(
        self,
        worker_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """
        Log out a user.
        
        Args:
            worker_id: Worker identifier
            ip_address: Client IP for audit
            request_id: Request ID for tracing
        """
        await self.audit_repo.log_logout(
            worker_id=worker_id,
            ip_address=ip_address,
            request_id=request_id
        )
        logger.info(f"User logged out: {worker_id}")
    
    async def request_password_reset(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Request a password reset for a user.
        
        Args:
            email: User's email
            ip_address: Client IP for audit
            
        Returns:
            True if reset token was sent (always returns True for security)
        """
        # Get user by email
        worker = await self.worker_repo.get_by_email(email)
        
        if not worker:
            # Don't reveal that user doesn't exist for security
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True
        
        # Create reset token
        token = create_password_reset_token(email)
        
        # Store token in database
        success = await self.worker_repo.set_password_reset_token(
            email=email,
            token=token,
            expires_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        
        if success:
            # Log password reset request
            await self.audit_repo.log_event(
                event_type="PASSWORD_RESET_REQUEST",
                action=f"Password reset requested for: {email}",
                worker_id=worker.worker_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            logger.info(f"Password reset token created for: {email}")
            
            # TODO: Send email with reset link
            # reset_link = f"{frontend_url}/reset-password?token={token}"
            
        return True
    
    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Reset password using a valid token.
        
        Args:
            token: Password reset token
            new_password: New password
            ip_address: Client IP for audit
            
        Returns:
            True if password was reset successfully
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        # Verify token and get email
        email = verify_password_reset_token(token)
        if not email:
            await self.audit_repo.log_event(
                event_type="PASSWORD_RESET",
                action="Failed password reset attempt - invalid token",
                ip_address=ip_address,
                status="FAILED",
                error_message="Invalid or expired token"
            )
            raise AuthenticationError("Invalid or expired reset token")
        
        # Get user by email
        worker = await self.worker_repo.get_by_email(email)
        if not worker:
            raise AuthenticationError("User not found")
        
        # Verify token matches database
        if worker.password_reset_token != token:
            raise AuthenticationError("Invalid reset token")
        
        # Check if token is expired
        if worker.password_reset_expires and worker.password_reset_expires < datetime.now(datetime.timezone.utc):
            raise AuthenticationError("Reset token has expired")
        
        # Reset password
        success = await self.worker_repo.reset_password(worker.worker_id, new_password)
        
        if success:
            # Log successful password reset
            await self.audit_repo.log_event(
                event_type="PASSWORD_RESET",
                action=f"Password reset successful for: {email}",
                worker_id=worker.worker_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            logger.info(f"Password reset successful for: {email}")
            
        return success
    
    async def change_password(
        self,
        worker_id: str,
        current_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Change password for authenticated user.
        
        Args:
            worker_id: Worker identifier
            current_password: Current password
            new_password: New password
            ip_address: Client IP for audit
            
        Returns:
            True if password was changed
            
        Raises:
            AuthenticationError: If current password is incorrect
        """
        success = await self.worker_repo.change_password(
            worker_id=worker_id,
            current_password=current_password,
            new_password=new_password
        )
        
        if success:
            await self.audit_repo.log_event(
                event_type="PASSWORD_CHANGE",
                action="Password changed",
                worker_id=worker_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            logger.info(f"Password changed for worker: {worker_id}")
        
        return success
    
    async def get_user_profile(self, worker_id: str) -> dict:
        """
        Get user profile information.
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Dictionary with user profile
            
        Raises:
            NotFoundError: If user not found
        """
        worker = await self.worker_repo.get_by_id(worker_id)
        if not worker:
            raise NotFoundError("HealthcareWorker", worker_id)
        
        return {
            "worker_id": worker.worker_id,
            "full_name": worker.full_name,
            "email": worker.email,
            "clinic_name": worker.clinic_name,
            "is_active": worker.is_active,
            "last_login_at": worker.last_login_at,
            "created_at": worker.created_at
        }