"""
ORM models for Visit and ScreeningData tables.

Visit          — one screening session (links patient ↔ worker ↔ data).
ScreeningData  — the clinical measurements entered for that visit.

These are separate tables (as in the ER diagram) because a visit is a
logical event while screening data is the clinical payload. This separation
also makes it easy to extend screening data fields without touching the
visit structure.

Key design notes
----------------
- weight_kg and height_m are stored so BMI can be recalculated if needed.
- bmi is stored as computed (not recalculated on every read).
- bmi_category is stored so it is always consistent with the bmi value.
  The backend computes it — the user never types this field manually.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.clinical_note import ClinicalNote
    from app.models.healthcare_worker import HealthcareWorker
    from app.models.patient import Patient
    from app.models.prediction import Prediction
    from app.models.report import Report


class Visit(Base, TimestampMixin):
    """
    Represents one screening visit.

    One patient can have many visits over time (longitudinal history FR-2.3).
    One visit produces exactly one Prediction and optionally one Report.
    """

    __tablename__ = "visits"

    # Primary key
    visit_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Foreign keys
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_id: Mapped[str] = mapped_column(
        ForeignKey("healthcare_workers.worker_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Visit metadata
    visit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of the screening visit",
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        back_populates="visits",
        lazy="select",
    )
    conducted_by: Mapped["HealthcareWorker"] = relationship(
        back_populates="visits",
        lazy="select",
    )
    screening_data: Mapped["ScreeningData"] = relationship(
        back_populates="visit",
        uselist=False,                # One-to-one
        cascade="all, delete-orphan",
        lazy="select",
    )
    prediction: Mapped[Optional["Prediction"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )
    report: Mapped[Optional["Report"]] = relationship(
        back_populates="visit",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )
    clinical_notes: Mapped[List["ClinicalNote"]] = relationship(
        back_populates="visit",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="ClinicalNote.created_at.desc()",
    )

    def __repr__(self) -> str:
        return (
            f"<Visit id={self.visit_id!r} "
            f"patient={self.patient_id!r} date={self.visit_date}>"
        )


class ScreeningData(Base):
    """
    Clinical measurements captured during a screening visit.

    Mandatory fields  : age, sex, weight_kg, height_m, bmi, bmi_category,
                        physical_activity, family_history, residence,
                        is_pregnant, has_hypertension.

    BMI and bmi_category are computed by the backend from weight + height.
    The user never inputs bmi_category manually.
    """

    __tablename__ = "screening_data"

    # Primary key (also FK to visits — one-to-one)
    screening_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    visit_id: Mapped[str] = mapped_column(
        ForeignKey("visits.visit_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,              # Enforces one-to-one with Visit
        index=True,
    )

    # Core anthropometric fields (always required)
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Patient age in years",
    )
    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Male | Female",
    )
    weight_kg: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Patient weight in kilograms",
    )
    height_m: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Patient height in metres",
    )

    # BMI fields — computed by the backend, never entered manually
    bmi: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="BMI = weight_kg / height_m². Computed by backend.",
    )
    bmi_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Normal | Overweight | Obese I | Obese II. Computed by backend.",
    )

    # Clinical boolean flags (required)
    is_pregnant: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    family_history_diabetes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="First-degree relative with diabetes",
    )
    previous_gdm: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Previous gestational diabetes mellitus",
    )
    physically_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Engages in regular physical activity",
    )
    has_hypertension: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    residence: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Urban | Rural",
    )

    # Relationship back to Visit
    visit: Mapped["Visit"] = relationship(
        back_populates="screening_data",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningData visit={self.visit_id!r} "
            f"bmi={self.bmi} category={self.bmi_category!r}>"
        )