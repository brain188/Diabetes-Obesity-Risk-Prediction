"""
Custom exception hierarchy for the application.

Using typed exceptions instead of generic ones gives:
  - Consistent HTTP status codes across the API
  - Clear, descriptive error messages in responses
  - Easy to catch and handle at different layers
"""

from typing import Any, Optional, Dict


class AppException(Exception):
    """
    Base exception for all application errors.
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        detail: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert exception to JSON response format."""
        response = {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.detail:
            response["detail"] = self.detail
        return response


# ──────────────────────────────────────────────────────────────────────────────
# Authentication & Authorization Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class AuthenticationError(AppException):
    """Invalid credentials or expired token."""
    
    def __init__(self, message: str = "Authentication failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            detail=detail,
        )


class InvalidTokenError(AppException):
    """JWT token is invalid, expired, or tampered with."""
    
    def __init__(self, message: str = "Invalid or expired token", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="INVALID_TOKEN",
            detail=detail,
        )


class InactiveUserError(AppException):
    """User account exists but has been deactivated."""
    
    def __init__(self, message: str = "User account is inactive", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="INACTIVE_USER",
            detail=detail,
        )


class AuthorizationError(AppException):
    """User lacks permission for the requested action."""
    
    def __init__(self, message: str = "Not authorized to perform this action", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            detail=detail,
        )


class PasswordResetTokenError(AppException):
    """Password reset token is invalid or expired."""
    
    def __init__(self, message: str = "Invalid or expired password reset token", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_RESET_TOKEN",
            detail=detail,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Resource Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class NotFoundError(AppException):
    """Requested resource does not exist."""
    
    def __init__(self, resource: str, identifier: Any, detail: Optional[Any] = None) -> None:
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            detail=detail or {"resource": resource, "identifier": str(identifier)},
        )


class DuplicateError(AppException):
    """Attempt to create a resource that already exists."""
    
    def __init__(self, resource: str, field: str, value: Any, detail: Optional[Any] = None) -> None:
        message = f"{resource} with {field}='{value}' already exists"
        super().__init__(
            message=message,
            status_code=409,
            error_code="DUPLICATE_RESOURCE",
            detail=detail or {"resource": resource, "field": field, "value": str(value)},
        )


# ──────────────────────────────────────────────────────────────────────────────
# Validation Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class InputValidationError(AppException):
    """
    Input data failed validation.
    Named to avoid clash with pydantic.ValidationError.
    """
    
    def __init__(self, message: str = "Input validation failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            detail=detail,
        )


class BusinessRuleError(AppException):
    """Business rule violation (e.g., invalid state transition)."""
    
    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="BUSINESS_RULE_VIOLATION",
            detail=detail,
        )


# ──────────────────────────────────────────────────────────────────────────────
# ML Prediction Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class PredictionError(AppException):
    """ML model prediction failed."""
    
    def __init__(self, message: str = "Prediction failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="PREDICTION_ERROR",
            detail=detail,
        )


class ModelNotLoadedError(AppException):
    """ML model artifacts are not loaded."""
    
    def __init__(self, message: str = "ML model is not loaded. Check model artifacts.", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="MODEL_NOT_LOADED",
            detail=detail,
        )


class FeatureMismatchError(AppException):
    """Input features don't match model expectations."""
    
    def __init__(self, message: str = "Feature mismatch between input and model", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=400,
            error_code="FEATURE_MISMATCH",
            detail=detail,
        )


class PreprocessingError(AppException):
    """Data preprocessing failed."""
    
    def __init__(self, message: str = "Data preprocessing failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="PREPROCESSING_ERROR",
            detail=detail,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Report Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class ReportGenerationError(AppException):
    """PDF report generation failed."""
    
    def __init__(self, message: str = "Report generation failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="REPORT_GENERATION_ERROR",
            detail=detail,
        )


class ReportNotFoundError(AppException):
    """Requested report file does not exist."""
    
    def __init__(self, report_id: str, detail: Optional[Any] = None) -> None:
        message = f"Report with id '{report_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="REPORT_NOT_FOUND",
            detail=detail or {"report_id": report_id},
        )


# ──────────────────────────────────────────────────────────────────────────────
# Database Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class DatabaseError(AppException):
    """Database operation failed."""
    
    def __init__(self, message: str = "Database operation failed", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            detail=detail,
        )


class DataIntegrityError(AppException):
    """Database integrity constraint violation."""
    
    def __init__(self, message: str = "Data integrity constraint violated", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="DATA_INTEGRITY_ERROR",
            detail=detail,
        )


# External Service Exceptions

class ExternalServiceError(AppException):
    """External service (e.g., PDF generator) failed."""
    
    def __init__(self, service: str, message: str = "External service error", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            detail=detail,
        )