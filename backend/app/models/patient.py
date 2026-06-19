"""
ORM model for the Patient table.

Maps to the Patient entity in the ER diagram.
A patient is registered by one healthcare worker and can have many
screening visits over time

Relationships
-------------
  registered_by → the worker who created this patient record (many-to-one)
  visits        → all screening visits for this patient      (one-to-many)
  clinical_notes → clinical notes for this patient           (one-to-many)
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Date, ForeignKey, Index, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.healthcare_worker import HealthcareWorker
    from app.models.screening_data import ScreeningVisit
    from app.models.clinical_note import ClinicalNote


class Patient(Base, TimestampMixin):
    """Patient model for storing patient demographic information."""
    
    __tablename__ = "patients"
    
    # Primary key
    patient_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="UUID primary key — auto-generated on registration"
    )
    
    # Foreign key: who registered this patient
    worker_id: Mapped[str] = mapped_column(
        ForeignKey("healthcare_workers.worker_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The healthcare worker who registered this patient"
    )
    
    # Patient identity
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,               # Indexed to support patient name search
        comment="Patient full name"
    )
    
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Patient date of birth"
    )
    
    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Patient biological sex: Male | Female"
    )
    
    contact_info: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Optional phone number or contact detail"
    )
    
    # Optional additional fields
    national_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
        comment="National ID or medical record number (optional)"
    )

     # Soft delete field
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Soft delete flag: True for active, False for deleted"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when patient was soft deleted"
    )
    
    # Relationships
    registered_by: Mapped["HealthcareWorker"] = relationship(
        back_populates="patients",
        lazy="select",
        doc="Healthcare worker who registered this patient"
    )
    
    screening_visits: Mapped[List["ScreeningVisit"]] = relationship(
        back_populates="patient",
        lazy="select",
        order_by="ScreeningVisit.visit_date.desc()",   # Most recent visit first
        cascade="all, delete-orphan",
        doc="All screening visits for this patient"
    )
    
    clinical_notes: Mapped[List["ClinicalNote"]] = relationship(
        back_populates="patient",
        lazy="select",
        order_by="ClinicalNote.created_at.desc()",
        cascade="all, delete-orphan",
        doc="Clinical notes for this patient"
    )
    
    # Hybrid Properties (computed fields)
    @hybrid_property
    def age(self) -> Optional[int]:
        """
        Calculate patient's current age from date of birth.
        Used as input feature for prediction models.
        """
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @age.expression
    def age(cls):
        """SQL expression for age calculation (for queries)."""
        # PostgreSQL age calculation
        return func.date_part('year', func.age(func.now(), cls.date_of_birth))
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_patient_name_search", "full_name"),
        Index("idx_patient_dob", "date_of_birth"),
        Index("idx_patient_registered_by", "worker_id"),
        Index("idx_patient_sex", "sex"),
        Index("idx_patient_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Patient id={self.patient_id!r} "
            f"name={self.full_name!r} sex={self.sex!r}>"
        )