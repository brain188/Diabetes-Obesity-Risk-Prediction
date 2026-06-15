"""
Clinical recommendation schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ClinicalGuidance(BaseModel):
    """Clinical guidance based on risk levels."""
    
    diabetes_guidance: str = Field(..., description="Diabetes-specific recommendations")
    obesity_guidance: str = Field(..., description="Obesity-specific recommendations")
    patient_advice: Optional[str] = Field(None, description="Patient-friendly advice")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "diabetes_guidance": "Monitor blood glucose regularly. Consider lifestyle modifications.",
                "obesity_guidance": "Maintain healthy BMI through balanced diet and exercise.",
                "patient_advice": "Eat more vegetables and exercise 30 minutes daily."
            }
        }
    )


class RecommendationResponse(BaseModel):
    """Response model for clinical recommendations."""
    
    recommendation_id: str = Field(..., description="Recommendation identifier")
    prediction_id: str = Field(..., description="Associated prediction identifier")
    priority: str = Field(..., description="Priority level (Urgent/High/Medium/Low)")
    action_text: str = Field(..., description="Detailed recommendation for healthcare worker")
    patient_advice: Optional[str] = Field(None, description="Patient-friendly advice")
    follow_up_interval_days: Optional[int] = Field(None, description="Days until follow-up")
    referral_required: Optional[str] = Field(None, description="Specialist referral needed")
    clinical_guidance: Optional[ClinicalGuidance] = Field(None, description="Detailed clinical guidance")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendation_id": "550e8400-e29b-41d4-a716-446655440005",
                "prediction_id": "550e8400-e29b-41d4-a716-446655440003",
                "priority": "Medium",
                "action_text": "Schedule follow-up in 3 months for glucose monitoring",
                "patient_advice": "Reduce sugar intake and increase physical activity",
                "follow_up_interval_days": 90,
                "referral_required": None,
                "clinical_guidance": None
            }
        }
    )