"""
Authentication and user management schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class UserRegisterRequest(BaseModel):
    """Request model for user registration."""
    
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="Valid email address")
    clinic_name: Optional[str] = Field(None, max_length=255, description="Healthcare facility name")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 characters)")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Dr. Jane Smith",
                "email": "jane.smith@clinic.org",
                "clinic_name": "City General Hospital",
                "password": "SecurePass123"
            }
        }
    )


class UserRegisterResponse(BaseModel):
    """Response model for user registration."""
    
    worker_id: str = Field(..., description="Unique worker identifier")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    clinic_name: Optional[str] = Field(None, description="Healthcare facility name")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "worker_id": "550e8400-e29b-41d4-a716-446655440000",
                "full_name": "Dr. Jane Smith",
                "email": "jane.smith@clinic.org",
                "clinic_name": "City General Hospital",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "jane.smith@clinic.org",
                "password": "SecurePass123"
            }
        }
    )


class UserLoginResponse(BaseModel):
    """Response model for successful login."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: "UserProfileResponse" = Field(..., description="User profile information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "worker_id": "550e8400-e29b-41d4-a716-446655440000",
                    "full_name": "Dr. Jane Smith",
                    "email": "jane.smith@clinic.org",
                    "clinic_name": "City General Hospital"
                }
            }
        }
    )


class TokenResponse(BaseModel):
    """Response model for token refresh."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenRefreshRequest(BaseModel):
    """Request model for refreshing access token."""
    
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Request model for initiating password reset."""
    
    email: EmailStr = Field(..., description="Registered email address")


class PasswordResetConfirmRequest(BaseModel):
    """Request model for confirming password reset."""
    
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordChangeRequest(BaseModel):
    """Request model for changing password (authenticated user)."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserProfileResponse(BaseModel):
    """Response model for user profile information."""
    
    worker_id: str = Field(..., description="Unique worker identifier")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    clinic_name: Optional[str] = Field(None, description="Healthcare facility name")
    is_active: bool = Field(..., description="Account active status")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "worker_id": "550e8400-e29b-41d4-a716-446655440000",
                "full_name": "Dr. Jane Smith",
                "email": "jane.smith@clinic.org",
                "clinic_name": "City General Hospital",
                "is_active": True,
                "last_login_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


# Update forward references
UserLoginResponse.model_rebuild()