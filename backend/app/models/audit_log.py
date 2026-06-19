"""
AuditLog model for tracking all security-relevant actions.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.healthcare_worker import HealthcareWorker


class AuditLog(Base, TimestampMixin): 
    """
    Audit trail for all user actions.
    Immutable log of security-relevant events for compliance.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    log_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        comment="Unique identifier for the audit log entry"
    )
    
    # ── Foreign key to healthcare worker (can be NULL for system events) ──────
    worker_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Healthcare worker who performed the action"
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of event (LOGIN, PREDICTION_RUN, REPORT_GENERATED, etc.)"
    )
    
    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Detailed action description"
    )
    
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of resource accessed (Patient, Report, etc.)"
    )
    
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Identifier of the resource accessed"
    )
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4 or IPv6)"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Client user agent string"
    )
    
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Correlation ID for request tracing"
    )
    
    # Outcome
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SUCCESS",
        comment="Outcome status: SUCCESS/FAILED"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if status is FAILED"
    )
    
    # Additional context (JSON)
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional JSON details about the event"
    )
    
    # Timestamps from TimestampMixin
    # created_at and updated_at are provided by TimestampMixin
    
    # Relationships
    healthcare_worker: Mapped[Optional["HealthcareWorker"]] = relationship(
        "HealthcareWorker",
        back_populates="audit_logs"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_audit_event_timestamp", "event_type", "created_at"),
        Index("idx_audit_worker_timestamp", "worker_id", "created_at"),
        Index("idx_audit_status", "status"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, event_type={self.event_type}, status={self.status})>"