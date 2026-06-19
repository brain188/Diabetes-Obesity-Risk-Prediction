"""
Patient management schemas.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PatientCreateRequest(BaseModel):
    """Request model for creating a new patient."""
    
    full_name: str = Field(..., min_length=2, max_length=200, description="Patient's full name")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    sex: str = Field(..., description="Patient's sex (Male/Female)")
    contact_info: Optional[str] = Field(None, max_length=200, description="Contact information")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID or medical record number")
    
    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        """Validate sex value."""
        v = v.capitalize()
        if v not in ["Male", "Female"]:
            raise ValueError("Sex must be either 'Male' or 'Female'")
        return v
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Ensure patient is at least 18 years old."""
        from datetime import date as today_date
        today = today_date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Patient must be at least 18 years old")
        if age > 120:
            raise ValueError("Invalid date of birth")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "date_of_birth": "1985-05-15",
                "sex": "Male",
                "contact_info": "+1234567890",
                "national_id": "ID12345678"
            }
        }
    )


class PatientUpdateRequest(BaseModel):
    """Request model for updating patient information."""
    
    full_name: Optional[str] = Field(None, min_length=2, max_length=200, description="Patient's full name")
    date_of_birth: Optional[date] = Field(None, description="Patient's date of birth")
    sex: Optional[str] = Field(None, description="Patient's sex (Male/Female)")
    contact_info: Optional[str] = Field(None, max_length=200, description="Contact information")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID or medical record number")
    
    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        """Validate sex value if provided."""
        if v is not None:
            v = v.capitalize()
            if v not in ["Male", "Female"]:
                raise ValueError("Sex must be either 'Male' or 'Female'")
        return v


class PatientResponse(BaseModel):
    """Response model for patient data."""
    
    patient_id: str = Field(..., description="Unique patient identifier")
    full_name: str = Field(..., description="Patient's full name")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    age: Optional[int] = Field(None, description="Calculated age")
    sex: str = Field(..., description="Patient's sex")
    contact_info: Optional[str] = Field(None, description="Contact information")
    national_id: Optional[str] = Field(None, description="National ID or medical record number")
    worker_id: str = Field(..., description="Healthcare worker who registered the patient")
    is_active: bool = Field(default=True, description="Whether the patient is active")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "full_name": "John Doe",
                "date_of_birth": "1985-05-15",
                "age": 39,
                "sex": "Male",
                "contact_info": "+1234567890",
                "national_id": "ID12345678",
                "worker_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class PatientListResponse(BaseModel):
    """Response model for patient list (paginated)."""
    
    patient_id: str = Field(..., description="Unique patient identifier")
    full_name: str = Field(..., description="Patient's full name")
    age: Optional[int] = Field(None, description="Calculated age")
    sex: str = Field(..., description="Patient's sex")
    is_active: bool = Field(default=True, description="Whether the patient is active")
    last_visit_date: Optional[datetime] = Field(None, description="Date of last screening visit")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "full_name": "John Doe",
                "age": 39,
                "sex": "Male",
                "is_active": True,
                "last_visit_date": "2024-01-15T10:30:00Z"
            }
        }
    )


class PatientSearchRequest(BaseModel):
    """Request model for searching patients."""
    
    query: str = Field(..., min_length=2, description="Search query (name or patient ID)")
    include_inactive: bool = Field(default=False, description="Include inactive patients")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "John",
                "include_inactive": False
            }
        }
    )