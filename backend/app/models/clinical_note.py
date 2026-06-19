"""
ClinicalNote model for free-text observations from healthcare workers.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.screening_data import ScreeningVisit
    from app.models.healthcare_worker import HealthcareWorker


class ClinicalNote(Base, TimestampMixin):
    """
    Free-text clinical notes written by healthcare workers.
    Provides additional context not captured by structured data.
    """
    
    __tablename__ = "clinical_notes"
    
    # Primary key
    note_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        comment="Unique identifier for the clinical note"
    )
    
    # Foreign keys
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient this note is about"
    )
    
    visit_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("screening_visits.visit_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional: Specific screening visit this note relates to"
    )
    
    author_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Healthcare worker who wrote the note"
    )
    
    # Note content
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional title/summary of the note"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full clinical note text"
    )
    
    # Metadata
    note_type: Mapped[str] = mapped_column(
        String(50),
        default="GENERAL",
        nullable=False,
        comment="Type of note: GENERAL, FOLLOW_UP, REFERRAL, etc."
    )
    
    is_urgent: Mapped[str] = mapped_column(
        String(20),
        default="NO",
        nullable=False,
        comment="Urgency flag: NO, YES, CRITICAL"
    )
    
    # Timestamps from TimestampMixin
    # created_at and updated_at are provided by TimestampMixin
    
    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="clinical_notes"
    )
    
    visit: Mapped[Optional["ScreeningVisit"]] = relationship(
        "ScreeningVisit",
        back_populates="clinical_note"
    )
    
    author: Mapped[Optional["HealthcareWorker"]] = relationship(
        "HealthcareWorker",
        back_populates="clinical_notes"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_clinical_note_patient", "patient_id", "created_at"),
        Index("idx_clinical_note_author", "author_id", "created_at"),
        Index("idx_clinical_note_visit", "visit_id"),
        Index("idx_clinical_note_type", "note_type"),
    )
    
    def __repr__(self) -> str:
        return f"<ClinicalNote(note_id={self.note_id}, patient_id={self.patient_id})>"