"""
AuditLog model for tracking all security-relevant actions.
"""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class AuditLog(Base):
    """
    Audit trail for all user actions.
    Immutable log of security-relevant events for compliance.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    log_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the audit log entry"
    )
    
    # Foreign key to healthcare worker (can be NULL for system events)
    worker_id = Column(
        UUID(as_uuid=False),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Healthcare worker who performed the action"
    )
    
    # Event details
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of event (LOGIN, PREDICTION_RUN, REPORT_GENERATED, etc.)"
    )
    
    action = Column(
        String(255),
        nullable=False,
        doc="Detailed action description"
    )
    
    resource_type = Column(
        String(50),
        nullable=True,
        doc="Type of resource accessed (Patient, Report, etc.)"
    )
    
    resource_id = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Identifier of the resource accessed"
    )
    
    # Request metadata
    ip_address = Column(
        String(45),
        nullable=True,
        doc="Client IP address (IPv4 or IPv6)"
    )
    
    user_agent = Column(
        String(500),
        nullable=True,
        doc="Client user agent string"
    )
    
    request_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Correlation ID for request tracing"
    )
    
    # Outcome
    status = Column(
        String(20),
        nullable=False,
        default="SUCCESS",
        doc="Outcome status: SUCCESS/FAILED"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        doc="Error message if status is FAILED"
    )
    
    # Additional context (JSON)
    details = Column(
        Text,
        nullable=True,
        doc="Additional JSON details about the event"
    )
    
    # Timestamp (uses base class created_at)
    
    # Relationships
    healthcare_worker = relationship(
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