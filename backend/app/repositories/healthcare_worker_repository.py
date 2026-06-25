"""
Repository for HealthcareWorker model operations.
"""

import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.core.security import hash_password, verify_password
from app.core.exceptions import AuthenticationError, DuplicateError, NotFoundError
from app.models.healthcare_worker import HealthcareWorker
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class HealthcareWorkerRepository(BaseRepository[HealthcareWorker]):
    """Repository for healthcare worker operations."""
    
    def __init__(self, session):
        super().__init__(HealthcareWorker, session)
    
    async def create_worker(
        self,
        full_name: str,
        email: str,
        password: str,
        clinic_name: Optional[str] = None,
        role: str = "healthcare_worker",
    ) -> HealthcareWorker:
        """
        Create a new healthcare worker account.
        
        Args:
            full_name: Worker's full name
            email: Email address (must be unique)
            password: Plain text password (will be hashed)
            clinic_name: Optional clinic/facility name
            
        Returns:
            Created HealthcareWorker instance
            
        Raises:
            DuplicateError: If email already exists
        """
        # Check if email already exists
        existing = await self.get_by_email(email)
        if existing:
            raise DuplicateError(
                resource="HealthcareWorker",
                field="email",
                value=email
            )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create worker
        worker = await self.create(
            full_name=full_name,
            email=email.lower(),
            password_hash=password_hash,
            clinic_name=clinic_name,
            role=role,
            is_active=True,
            is_verified=True,
        )
        
        logger.info(f"Created healthcare worker: {email}")
        return worker
    
    async def get_by_email(self, email: str) -> Optional[HealthcareWorker]:
        """Get healthcare worker by email address."""
        try:
            stmt = select(HealthcareWorker).where(
                HealthcareWorker.email == email.lower()
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get worker by email {email}: {str(e)}")
            raise
    
    async def authenticate(self, email: str, password: str) -> HealthcareWorker:
        """
        Authenticate a healthcare worker.
        
        Args:
            email: Email address
            password: Plain text password
            
        Returns:
            Authenticated HealthcareWorker instance
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        worker = await self.get_by_email(email)
        
        if not worker:
            raise AuthenticationError("Invalid email or password")
        
        if not worker.is_active:
            raise AuthenticationError("Account is deactivated")
        
        if not verify_password(password, worker.password_hash):
            raise AuthenticationError("Invalid email or password")
        
        # Update last login timestamp
        await self.update_last_login(worker.worker_id)
        
        logger.info(f"Authenticated worker: {email}")
        return worker
    
    async def update_last_login(self, worker_id: str) -> None:
        """Update the last login timestamp for a worker."""
        try:
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(last_login_at=datetime.now(timezone.utc))
            await self.session.execute(stmt)
            await self.session.flush()
        except Exception as e:
            logger.error(f"Failed to update last login for {worker_id}: {str(e)}")

    # ── Refresh Token Methods ──────────────────────────────────────────────────
    
    async def store_refresh_token(self, worker_id: str, token_hash: str, expires_at: datetime) -> bool:
        """
        Store a refresh token hash for a worker.
        
        Args:
            worker_id: Worker identifier
            token_hash: SHA-256 hash of the refresh token
            expires_at: Token expiration time
            
        Returns:
            True if successful
        """
        try:
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(
                refresh_token=token_hash,
                refresh_token_expires=expires_at
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to store refresh token for {worker_id}: {str(e)}")
            return False
    
    async def validate_refresh_token(self, worker_id: str, raw_token: str) -> bool:
        """
        Validate a refresh token against the stored hash.
        
        Args:
            worker_id: Worker identifier
            raw_token: Raw refresh token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Get worker with refresh token
            stmt = select(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id,
                HealthcareWorker.refresh_token.isnot(None)
            )
            result = await self.session.execute(stmt)
            worker = result.scalar_one_or_none()
            
            if not worker:
                return False
            
            # Check if token is expired
            if worker.refresh_token_expires and worker.refresh_token_expires < datetime.utcnow():
                logger.warning(f"Refresh token expired for user {worker_id}")
                return False
            
            # Hash the incoming token and compare with stored hash
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            return token_hash == worker.refresh_token
        
        except Exception as e:
            logger.error(f"Failed to validate refresh token for {worker_id}: {str(e)}")
            return False
    
    async def revoke_refresh_token(self, worker_id: str) -> bool:
        """
        Revoke the current refresh token for a worker.
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            True if successful
        """
        try:
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(
                refresh_token=None,
                refresh_token_expires=None
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Revoked refresh token for user {worker_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke refresh token for {worker_id}: {str(e)}")
            return False
    
    # ── Password Reset Methods ──────────────────────────────────────────────────
    
    async def set_password_reset_token(self, email: str, token: str, expires_minutes: int = 30) -> bool:
        """
        Set password reset token for a worker.
        
        Args:
            email: Worker's email
            token: Reset token
            expires_minutes: Token expiry in minutes
            
        Returns:
            True if successful, False if worker not found
        """
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.email == email.lower()
            ).values(
                password_reset_token=token,
                password_reset_expires=expires_at
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to set reset token for {email}: {str(e)}")
            return False
    
    async def verify_reset_token(self, token: str) -> Optional[HealthcareWorker]:
        """
        Verify a password reset token and return the worker.
        
        Args:
            token: Reset token to verify
            
        Returns:
            HealthcareWorker if token is valid, None otherwise
        """
        try:
            stmt = select(HealthcareWorker).where(
                HealthcareWorker.password_reset_token == token,
                HealthcareWorker.password_reset_expires > datetime.now(timezone.utc)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to verify reset token: {str(e)}")
            return None
    
    async def reset_password(self, worker_id: str, new_password: str) -> bool:
        """
        Reset a worker's password.
        
        Args:
            worker_id: Worker identifier
            new_password: New plain text password
            
        Returns:
            True if successful
        """
        try:
            password_hash = hash_password(new_password)
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(
                password_hash=password_hash,
                password_reset_token=None,
                password_reset_expires=None
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Reset password for worker: {worker_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to reset password for {worker_id}: {str(e)}")
            return False
    
    async def change_password(self, worker_id: str, current_password: str, new_password: str) -> bool:
        """
        Change a worker's password (requires current password).
        
        Args:
            worker_id: Worker identifier
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            AuthenticationError: If current password is incorrect
        """
        worker = await self.get_by_id(worker_id)
        if not worker:
            raise NotFoundError("HealthcareWorker", worker_id)
        
        if not verify_password(current_password, worker.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        return await self.reset_password(worker_id, new_password)
    
    async def deactivate_account(self, worker_id: str) -> bool:
        """Deactivate a healthcare worker account."""
        try:
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(is_active=False)
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Deactivated worker account: {worker_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate account {worker_id}: {str(e)}")
            return False
    
    async def activate_account(self, worker_id: str) -> bool:
        """Activate a healthcare worker account."""
        try:
            stmt = update(HealthcareWorker).where(
                HealthcareWorker.worker_id == worker_id
            ).values(is_active=True)
            result = await self.session.execute(stmt)
            await self.session.flush()

            if result.rowcount > 0:
                logger.info(f"Activated worker account: {worker_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to activate account {worker_id}: {str(e)}")
            return False

    async def list_workers(self) -> list[HealthcareWorker]:
        """Return all registered healthcare workers ordered by creation date."""
        result = await self.session.execute(
            select(HealthcareWorker).order_by(HealthcareWorker.created_at.desc())
        )
        return list(result.scalars().all())