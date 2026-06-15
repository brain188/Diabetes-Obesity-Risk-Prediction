"""
Repositories module for database access layer.
Provides clean abstraction for CRUD operations.
"""

from app.repositories.base import BaseRepository
from app.repositories.healthcare_worker_repository import HealthcareWorkerRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.clinical_note_repository import ClinicalNoteRepository
from app.repositories.report_repository import ReportRepository

__all__ = [
    "BaseRepository",
    "HealthcareWorkerRepository",
    "PatientRepository",
    "ScreeningRepository",
    "PredictionRepository",
    "AuditLogRepository",
    "ClinicalNoteRepository",
    "ReportRepository",
]