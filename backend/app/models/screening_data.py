"""
ScreeningVisit and ScreeningData models for capturing patient screening information.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, 
    Index, Integer, String, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.prediction import Prediction
    from app.models.clinical_note import ClinicalNote
    from app.models.report import Report


class ScreeningVisit(Base, TimestampMixin):
    """
    A single screening session for a patient.
    Groups together screening data, predictions, and reports.
    """
    
    __tablename__ = "screening_visits"
    
    # Primary key
    visit_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Unique identifier for the screening visit"
    )
    
    # Foreign keys
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient associated with this visit"
    )
    
    # Visit information
    visit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(datetime.timezone.utc),
        nullable=False,
        comment="Date and time of the screening visit"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Optional notes about the screening visit"
    )
    
    # Relationships
    patient: Mapped["Patient"] = relationship(
        back_populates="screening_visits"
    )
    
    screening_data: Mapped[Optional["ScreeningData"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Screening data for this visit"
    )
    
    prediction: Mapped[Optional["Prediction"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Prediction results for this visit"
    )
    
    report: Mapped[Optional["Report"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Generated report for this visit"
    )
    
    clinical_note: Mapped[Optional["ClinicalNote"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Clinical note for this visit"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_visit_patient_date", "patient_id", "visit_date"),
        Index("idx_visit_date", "visit_date"),
    )
    
    def __repr__(self) -> str:
        return f"<ScreeningVisit(visit_id={self.visit_id}, patient_id={self.patient_id})>"


class ScreeningData(Base, TimestampMixin):
    """
    Clinical measurements and risk factors collected during screening.
    This data is used as input for the prediction models.
    """
    
    __tablename__ = "screening_data"
    
    # Primary key (same as visit_id for one-to-one relationship)
    visit_id: Mapped[str] = mapped_column(
        ForeignKey("screening_visits.visit_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to screening visit"
    )
    
    # Anthropometric measurements
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Weight in kilograms (kg)"
    )
    
    height: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Height in meters (m)"
    )
    
    bmi: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Body Mass Index (calculated from weight/height²)"
    )
    
    bmi_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="BMI category (Normal/Overweight/Obese I/Obese II+)"
    )
    
    # Lifestyle factors
    physical_activity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Physical activity level (days per week, 0-7)"
    )
    
    # Medical history (boolean flags)
    family_history_diabetes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether patient has family history of diabetes"
    )
    
    previous_gdm: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether patient had Gestational Diabetes Mellitus (for female patients)"
    )
    
    has_hypertension: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether patient has hypertension"
    )
    
    # Additional features
    is_pregnant: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether the patient is currently pregnant"
    )
    
    residence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Rural",
        comment="Residence type (Urban/Rural)"
    )
    
    # Computed/derived fields
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Patient's age at time of screening (calculated from date of birth)"
    )
    
    # Model version tracking
    model_version_used: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Version of the model used for preprocessing/prediction"
    )
    
    # Relationships
    visit: Mapped["ScreeningVisit"] = relationship(
        back_populates="screening_data"
    )
    
    # Indexes and constraints
    __table_args__ = (
        CheckConstraint("weight >= 20 AND weight <= 300", name="ck_weight_range"),
        CheckConstraint("height >= 1.0 AND height <= 2.5", name="ck_height_range"),
        CheckConstraint("bmi >= 10 AND bmi <= 70", name="ck_bmi_range"),
        CheckConstraint("age >= 18 AND age <= 100", name="ck_age_range"),
        Index("idx_screening_visit", "visit_id"),
    )
    
    def __repr__(self) -> str:
        return f"<ScreeningData(visit_id={self.visit_id}, bmi={self.bmi})>"