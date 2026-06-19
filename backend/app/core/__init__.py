"""
Core module for the Intelligent DSS application.
Contains configuration, database setup, security, logging, exceptions, and constants.
"""

from app.core.config import settings, get_settings
from app.core.constants import (
    # Risk
    RISK_LOW,
    RISK_MODERATE,
    RISK_HIGH,
    RISK_COLORS,
    # Remove these - they don't exist
    # RISK_THRESHOLD_LOW,
    # RISK_THRESHOLD_MODERATE,
    # RISK_THRESHOLD_HIGH,
    # BMI
    BMI_NORMAL_MAX,
    BMI_OVERWEIGHT_MAX,
    BMI_OBESE_I_MAX,
    BMI_CAT_NORMAL,
    BMI_CAT_OVERWEIGHT,
    BMI_CAT_OBESE_I,
    BMI_CAT_OBESE_II,
    BMI_CATEGORIES,
    BMI_TO_RISK,
    # Diabetes
    DIABETES_CLASSES,
    DIABETES_CLASSES_ENCODE,
    # Audit
    AUDIT_LOGIN,
    AUDIT_LOGOUT,
    AUDIT_LOGIN_FAILED,
    AUDIT_REGISTER,
    AUDIT_PATIENT_CREATED,
    AUDIT_PATIENT_UPDATED,
    AUDIT_PATIENT_VIEWED,
    AUDIT_SCREENING_DONE,
    AUDIT_PREDICTION_RUN,
    AUDIT_REPORT_GENERATED,
    AUDIT_REPORT_DOWNLOADED,
    AUDIT_PASSWORD_RESET,
    AUDIT_PASSWORD_RESET_REQUEST,
    AUDIT_SESSION_EXPIRED,
    AUDIT_CLINICAL_NOTE_ADDED,
    AUDIT_EVENT_TYPES,
    # Pagination
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    # Validation ranges
    WEIGHT_MIN_KG,
    WEIGHT_MAX_KG,
    HEIGHT_MIN_M,
    HEIGHT_MAX_M,
    AGE_MIN,
    AGE_MAX,
    BMI_MIN,
    BMI_MAX,
    # Helper functions
    get_risk_color,
    get_bmi_category,
    get_obesity_risk_from_bmi,
    get_diabetes_class_name,
    get_diabetes_class_id,
    is_valid_bmi,
    is_valid_age,
    is_valid_weight,
    is_valid_height,
)
from app.core.database import (
    Base,
    init_database,
    close_database,
    get_db_session,
    get_engine,
    get_session_maker,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    verify_token_expiration,
    create_password_reset_token,
    verify_password_reset_token,
    raise_unauthorized,
    raise_forbidden,
)
from app.core.logging import setup_logging, get_logger, audit_logger
from app.core.exceptions import (
    # Base
    AppException,
    # Authentication
    AuthenticationError,
    InvalidTokenError,
    InactiveUserError,
    AuthorizationError,
    PasswordResetTokenError,
    # Resource
    NotFoundError,
    DuplicateError,
    # Validation
    InputValidationError,
    BusinessRuleError,
    # ML Prediction
    PredictionError,
    ModelNotLoadedError,
    FeatureMismatchError,
    PreprocessingError,
    # Report
    ReportGenerationError,
    ReportNotFoundError,
    # Database
    DatabaseError,
    DataIntegrityError,
    # External
    ExternalServiceError,
)
from app.core.dependencies import (
    get_current_user_id,
    get_optional_user_id,
    get_client_ip,
    get_request_metadata,
    ConfigDep,
    DbSessionDep,
    CurrentUserDep,
    OptionalUserDep,
    ClientIpDep,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Constants - Risk
    "RISK_LOW",
    "RISK_MODERATE",
    "RISK_HIGH",
    "RISK_COLORS",
    # Constants - BMI
    "BMI_NORMAL_MAX",
    "BMI_OVERWEIGHT_MAX",
    "BMI_OBESE_I_MAX",
    "BMI_CAT_NORMAL",
    "BMI_CAT_OVERWEIGHT",
    "BMI_CAT_OBESE_I",
    "BMI_CAT_OBESE_II",
    "BMI_CATEGORIES",
    "BMI_TO_RISK",
    # Constants - Diabetes
    "DIABETES_CLASSES",
    "DIABETES_CLASSES_ENCODE",
    # Constants - Audit
    "AUDIT_LOGIN",
    "AUDIT_LOGOUT",
    "AUDIT_LOGIN_FAILED",
    "AUDIT_REGISTER",
    "AUDIT_PATIENT_CREATED",
    "AUDIT_PATIENT_UPDATED",
    "AUDIT_PATIENT_VIEWED",
    "AUDIT_SCREENING_DONE",
    "AUDIT_PREDICTION_RUN",
    "AUDIT_REPORT_GENERATED",
    "AUDIT_REPORT_DOWNLOADED",
    "AUDIT_PASSWORD_RESET",
    "AUDIT_PASSWORD_RESET_REQUEST",
    "AUDIT_SESSION_EXPIRED",
    "AUDIT_CLINICAL_NOTE_ADDED",
    "AUDIT_EVENT_TYPES",
    # Constants - Pagination
    "DEFAULT_PAGE",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    # Constants - Validation Ranges
    "WEIGHT_MIN_KG",
    "WEIGHT_MAX_KG",
    "HEIGHT_MIN_M",
    "HEIGHT_MAX_M",
    "AGE_MIN",
    "AGE_MAX",
    "BMI_MIN",
    "BMI_MAX",
    # Constants - Helper Functions
    "get_risk_color",
    "get_bmi_category",
    "get_obesity_risk_from_bmi",
    "get_diabetes_class_name",
    "get_diabetes_class_id",
    "is_valid_bmi",
    "is_valid_age",
    "is_valid_weight",
    "is_valid_height",
    # Database
    "Base",
    "init_database",
    "close_database",
    "get_db_session",
    "get_engine",
    "get_session_maker",
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "verify_token_expiration",
    "create_password_reset_token",
    "verify_password_reset_token",
    "raise_unauthorized",
    "raise_forbidden",
    # Logging
    "setup_logging",
    "get_logger",
    "audit_logger",
    # Exceptions
    "AppException",
    "AuthenticationError",
    "InvalidTokenError",
    "InactiveUserError",
    "AuthorizationError",
    "PasswordResetTokenError",
    "NotFoundError",
    "DuplicateError",
    "InputValidationError",
    "BusinessRuleError",
    "PredictionError",
    "ModelNotLoadedError",
    "FeatureMismatchError",
    "PreprocessingError",
    "ReportGenerationError",
    "ReportNotFoundError",
    "DatabaseError",
    "DataIntegrityError",
    "ExternalServiceError",
    # Dependencies
    "get_current_user_id",
    "get_optional_user_id",
    "get_client_ip",
    "get_request_metadata",
    "ConfigDep",
    "DbSessionDep",
    "CurrentUserDep",
    "OptionalUserDep",
    "ClientIpDep",
]