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