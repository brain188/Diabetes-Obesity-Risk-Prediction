"""
ClinicalNote model for free-text observations from healthcare workers.
"""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class ClinicalNote(Base):
    """
    Free-text clinical notes written by healthcare workers.
    Provides additional context not captured by structured data.
    """
    
    __tablename__ = "clinical_notes"
    
    # Primary key
    note_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the clinical note"
    )
    
    # Foreign keys
    patient_id = Column(
        UUID(as_uuid=False),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Patient this note is about"
    )
    
    visit_id = Column(
        UUID(as_uuid=False),
        ForeignKey("screening_visits.visit_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional: Specific screening visit this note relates to"
    )
    
    author_id = Column(
        UUID(as_uuid=False),
        ForeignKey("healthcare_workers.worker_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Healthcare worker who wrote the note"
    )
    
    # Note content
    title = Column(
        String(255),
        nullable=True,
        doc="Optional title/summary of the note"
    )
    
    content = Column(
        Text,
        nullable=False,
        doc="Full clinical note text"
    )
    
    # Metadata
    note_type = Column(
        String(50),
        default="GENERAL",
        nullable=False,
        doc="Type of note: GENERAL, FOLLOW_UP, REFERRAL, etc."
    )
    
    is_urgent = Column(
        String(20),
        default="NO",
        nullable=False,
        doc="Urgency flag: NO, YES, CRITICAL"
    )
    
    # Timestamps (uses base created_at and updated_at)
    
    # Relationships
    patient = relationship(
        "Patient",
        back_populates="clinical_notes"
    )
    
    visit = relationship(
        "ScreeningVisit",
        back_populates="clinical_note"
    )
    
    author = relationship(
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