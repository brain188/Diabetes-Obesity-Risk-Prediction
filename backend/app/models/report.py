"""
Report model for generated PDF/JSON reports.
"""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class Report(Base):
    """
    Generated patient report (PDF or JSON).
    Stores metadata about generated reports.
    """
    
    __tablename__ = "reports"
    
    # Primary key
    report_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the report"
    )
    
    # Foreign keys
    visit_id = Column(
        UUID(as_uuid=False),
        ForeignKey("screening_visits.visit_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One report per visit
        index=True,
        doc="Screening visit this report belongs to"
    )
    
    generated_by = Column(
        UUID(as_uuid=False),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        doc="Healthcare worker who generated the report"
    )
    
    # Report metadata
    format = Column(
        String(10),
        default="PDF",
        nullable=False,
        doc="Report format: PDF or JSON"
    )
    
    file_path = Column(
        String(500),
        nullable=False,
        doc="Path to the stored report file"
    )
    
    file_size_bytes = Column(
        String(20),
        nullable=True,
        doc="Size of the report file"
    )
    
    generated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(datetime.timezone.utc),
        nullable=False,
        doc="Timestamp when report was generated"
    )
    
    downloaded_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when report was last downloaded"
    )
    
    download_count = Column(
        String(20),
        default="0",
        nullable=False,
        doc="Number of times report has been downloaded"
    )
    
    # Checksum for integrity verification
    checksum = Column(
        String(64),
        nullable=True,
        doc="SHA-256 checksum of the report file"
    )
    
    # Relationships
    visit = relationship(
        "ScreeningVisit",
        back_populates="report"
    )
    
    healthcare_worker = relationship(
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