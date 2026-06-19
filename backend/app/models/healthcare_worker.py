"""
HealthcareWorker model for system users.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.audit_log import AuditLog
    from app.models.clinical_note import ClinicalNote


class HealthcareWorker(Base, TimestampMixin):
    """
    Healthcare worker who uses the system.
    Stores authentication and profile information.
    """
    
    __tablename__ = "healthcare_workers"
    
    # Primary key
    worker_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Unique identifier for the healthcare worker"
    )
    
    # Personal information
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name of the healthcare worker"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email address (used for login)"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    clinic_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the healthcare facility"
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email has been verified"
    )
    
    # Session tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful login"
    )

    # Refresh Token
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Current valid refresh token (hashed)"
    )
    
    refresh_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration time for refresh token"
    )
    
    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Token for password reset (temporary)"
    )
    
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration time for password reset token"
    )
    
    # Relationships
    patients: Mapped[List["Patient"]] = relationship(
        back_populates="registered_by",
        lazy="select",
        doc="Patients registered by this worker"
    )
    
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="healthcare_worker",
        lazy="select",
        doc="Audit logs for actions by this worker"
    )
    
    clinical_notes: Mapped[List["ClinicalNote"]] = relationship(
        back_populates="author",
        lazy="select",
        doc="Clinical notes written by this worker"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_hw_email_active", "email", "is_active"),
        Index("idx_hw_created_at", "created_at"),
        Index("idx_hw_refresh_token", "refresh_token"),
    )
    
    def __repr__(self) -> str:
        return f"<HealthcareWorker(worker_id={self.worker_id}, email={self.email})>"