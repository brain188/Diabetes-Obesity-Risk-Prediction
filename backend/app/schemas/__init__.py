"""
Schemas module for Pydantic request/response models.
Handles data validation, serialization, and deserialization.
"""

# Common schemas
from app.schemas.common import (
    HealthCheckResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)

# Authentication schemas
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    TokenResponse,
    TokenRefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    PasswordChangeRequest,
    UserProfileResponse,
)

# Patient schemas
from app.schemas.patient import (
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    PatientListResponse,
    PatientSearchRequest,
)

# Screening schemas
from app.schemas.screening import (
    ScreeningDataRequest,
    ScreeningDataResponse,
    ScreeningVisitResponse,
    ScreeningVisitListResponse,
)

# Prediction schemas
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    DiabetesPrediction,
    ObesityPrediction,
    RiskClassification,
)

# SHAP explanation schemas
from app.schemas.shap import (
    SHAPExplanationResponse,
    FeatureContribution,
    GlobalFeatureImportanceResponse,
)

# Recommendation schemas
from app.schemas.recommendation import (
    RecommendationResponse,
    ClinicalGuidance,
)

# Clinical note schemas
from app.schemas.clinical_note import (
    ClinicalNoteCreateRequest,
    ClinicalNoteUpdateRequest,
    ClinicalNoteResponse,
    ClinicalNoteListResponse,
)

# Report schemas
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportDownloadResponse,
)

__all__ = [
    # Common
    "HealthCheckResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    # Auth
    "UserRegisterRequest",
    "UserRegisterResponse",
    "UserLoginRequest",
    "UserLoginResponse",
    "TokenResponse",
    "TokenRefreshRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "PasswordChangeRequest",
    "UserProfileResponse",
    # Patient
    "PatientCreateRequest",
    "PatientUpdateRequest",
    "PatientResponse",
    "PatientListResponse",
    "PatientSearchRequest",
    # Screening
    "ScreeningDataRequest",
    "ScreeningDataResponse",
    "ScreeningVisitResponse",
    "ScreeningVisitListResponse",
    # Prediction
    "PredictionRequest",
    "PredictionResponse",
    "DiabetesPrediction",
    "ObesityPrediction",
    "RiskClassification",
    # SHAP
    "SHAPExplanationResponse",
    "FeatureContribution",
    "GlobalFeatureImportanceResponse",
    # Recommendation
    "RecommendationResponse",
    "ClinicalGuidance",
    # Clinical Notes
    "ClinicalNoteCreateRequest",
    "ClinicalNoteUpdateRequest",
    "ClinicalNoteResponse",
    "ClinicalNoteListResponse",
    # Report
    "ReportGenerateRequest",
    "ReportResponse",
    "ReportDownloadResponse",
]