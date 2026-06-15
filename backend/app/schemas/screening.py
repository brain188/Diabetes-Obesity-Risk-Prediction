"""
Screening data capture schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ScreeningDataRequest(BaseModel):
    """Request model for entering screening data."""
    
    # Anthropometric measurements
    weight: float = Field(..., ge=20, le=300, description="Weight in kilograms")
    height: float = Field(..., ge=1.0, le=2.5, description="Height in meters")
    
    # Clinical measurements (optional)
    glucose_level: Optional[float] = Field(None, ge=40, le=600, description="Blood glucose level (mg/dL)")
    blood_pressure: Optional[str] = Field(None, pattern=r'^\d{2,3}/\d{2,3}$', description="Blood pressure (e.g., '120/80')")
    
    # Lifestyle factors
    physical_activity: bool = Field(default=False, description="Physical activity")
    
    # Medical history
    family_history_diabetes: bool = Field(default=False, description="Family history of diabetes")
    previous_gdm: bool = Field(default=False, description="Previous Gestational Diabetes Mellitus")
    has_hypertension: bool = Field(default=False, description="Has hypertension")
    
    # Additional features
    is_pregnant: bool = Field(default=False, description="Currently pregnant")
    residence: str = Field(default="Rural", description="Residence type (Urban/Rural)")
    
    # Optional notes
    notes: Optional[str] = Field(None, max_length=1000, description="Additional screening notes")
    
    @field_validator("residence")
    @classmethod
    def validate_residence(cls, v: str) -> str:
        """Validate residence value."""
        v = v.capitalize()
        if v not in ["Urban", "Rural"]:
            raise ValueError("Residence must be either 'Urban' or 'Rural'")
        return v
    
    @field_validator("blood_pressure")
    @classmethod
    def validate_blood_pressure(cls, v: Optional[str]) -> Optional[str]:
        """Validate blood pressure format."""
        if v is not None:
            import re
            if not re.match(r'^\d{2,3}/\d{2,3}$', v):
                raise ValueError("Blood pressure must be in format '120/80'")
            systolic, diastolic = map(int, v.split('/'))
            if systolic < 70 or systolic > 250:
                raise ValueError("Systolic pressure must be between 70 and 250")
            if diastolic < 40 or diastolic > 150:
                raise ValueError("Diastolic pressure must be between 40 and 150")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "weight": 75.5,
                "height": 1.75,
                "glucose_level": 95.0,
                "blood_pressure": "120/80",
                "physical_activity": True,
                "family_history_diabetes": True,
                "previous_gdm": False,
                "has_hypertension": False,
                "is_pregnant": False,
                "residence": "Urban",
                "notes": "Patient reports increased thirst"
            }
        }
    )


class ScreeningDataResponse(BaseModel):
    """Response model for screening data."""
    
    visit_id: str = Field(..., description="Screening visit identifier")
    weight: float = Field(..., description="Weight in kilograms")
    height: float = Field(..., description="Height in meters")
    bmi: float = Field(..., description="Calculated BMI")
    bmi_category: str = Field(..., description="BMI category")
    glucose_level: Optional[float] = Field(None, description="Blood glucose level")
    blood_pressure: Optional[str] = Field(None, description="Blood pressure")
    physical_activity: bool = Field(..., description="Physically active")
    family_history_diabetes: bool = Field(..., description="Family history of diabetes")
    previous_gdm: bool = Field(..., description="Previous GDM")
    has_hypertension: bool = Field(..., description="Has hypertension")
    is_pregnant: bool = Field(..., description="Currently pregnant")
    residence: str = Field(..., description="Residence type")
    age: int = Field(..., description="Patient age at screening")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "weight": 75.5,
                "height": 1.75,
                "bmi": 24.65,
                "bmi_category": "Normal",
                "glucose_level": 95.0,
                "blood_pressure": "120/80",
                "physical_activity": True,
                "family_history_diabetes": True,
                "previous_gdm": False,
                "has_hypertension": False,
                "is_pregnant": False,
                "residence": "Urban",
                "age": 39,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class ScreeningVisitResponse(BaseModel):
    """Response model for a complete screening visit."""
    
    visit_id: str = Field(..., description="Screening visit identifier")
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Patient's full name")
    visit_date: datetime = Field(..., description="Visit timestamp")
    screening_data: Optional[ScreeningDataResponse] = Field(None, description="Screening measurements")
    notes: Optional[str] = Field(None, description="Visit notes")
    created_at: datetime = Field(..., description="Record creation timestamp")


class ScreeningVisitListResponse(BaseModel):
    """Response model for screening visit list."""
    
    visit_id: str = Field(..., description="Screening visit identifier")
    visit_date: datetime = Field(..., description="Visit timestamp")
    bmi: Optional[float] = Field(None, description="BMI at screening")
    diabetes_risk: Optional[str] = Field(None, description="Diabetes risk level")
    obesity_risk: Optional[str] = Field(None, description="Obesity risk level")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "visit_date": "2024-01-15T10:30:00Z",
                "bmi": 24.65,
                "diabetes_risk": "Moderate",
                "obesity_risk": "Low"
            }
        }
    )