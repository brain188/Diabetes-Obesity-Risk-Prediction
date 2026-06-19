"""
Report model for generated PDF/JSON reports.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.screening_data import ScreeningVisit
    from app.models.healthcare_worker import HealthcareWorker


class Report(Base, TimestampMixin):
    """
    Generated patient report (PDF or JSON).
    Stores metadata about generated reports.
    """
    
    __tablename__ = "reports"
    
    # Primary key
    report_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        comment="Unique identifier for the report"
    )
    
    # Foreign keys
    visit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("screening_visits.visit_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Screening visit this report belongs to"
    )
    
    generated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        comment="Healthcare worker who generated the report"
    )
    
    # Report metadata
    format: Mapped[str] = mapped_column(
        String(10),
        default="PDF",
        nullable=False,
        comment="Report format: PDF or JSON"
    )
    
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Path to the stored report file"
    )
    
    file_size_bytes: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Size of the report file"
    )
    
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when report was generated"
    )
    
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when report was last downloaded"
    )
    
    download_count: Mapped[str] = mapped_column(
        String(20),
        default="0",
        nullable=False,
        comment="Number of times report has been downloaded"
    )
    
    # Checksum for integrity verification
    checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 checksum of the report file"
    )
    
    # Timestamps from TimestampMixin
    # created_at and updated_at are provided by TimestampMixin
    
    # Relationships
    visit: Mapped["ScreeningVisit"] = relationship(
        "ScreeningVisit",
        back_populates="report"
    )
    
    healthcare_worker: Mapped[Optional["HealthcareWorker"]] = relationship(
        "HealthcareWorker",
        doc="Healthcare worker who generated the report"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_report_visit", "visit_id"),
        Index("idx_report_generated_at", "generated_at"),
        Index("idx_report_format", "format"),
    )
    
    def __repr__(self) -> str:
        return f"<Report(report_id={self.report_id}, format={self.format})>"