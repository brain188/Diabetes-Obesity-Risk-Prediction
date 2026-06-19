"""
Models module for SQLAlchemy ORM entities.
All database tables are defined here.
"""

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

# Import ALL models to register them with Base.metadata
from app.models.healthcare_worker import HealthcareWorker
from app.models.patient import Patient
from app.models.screening_data import ScreeningData, ScreeningVisit
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.explanation import SHAPExplanation
from app.models.audit_log import AuditLog
from app.models.clinical_note import ClinicalNote
from app.models.report import Report

__all__ = [
    "Base",
    "TimestampMixin",
    "generate_uuid",
    "HealthcareWorker",
    "Patient",
    "ScreeningData",
    "ScreeningVisit",
    "Prediction",
    "Recommendation",
    "SHAPExplanation",
    "AuditLog",
    "ClinicalNote",
    "Report",
]