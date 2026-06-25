"""
Risk prediction schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.screening import ScreeningDataRequest
from app.schemas.recommendation import RecommendationResponse
from app.schemas.shap import (
    SHAPExplanationResponse, 
    LIMEExplanationResponse, 
    GlobalFeatureImportanceResponse
) 

class RiskClassification(BaseModel):
    """Risk classification details."""
    
    probability: float = Field(..., ge=0, le=1, description="Risk probability (0-1)")
    risk_class: str = Field(..., description="Risk class (Low/Moderate/High)")
    risk_color: str = Field(..., description="Color code for UI")
    class_label: Optional[str] = Field(None, description="Detailed class label (for diabetes)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "probability": 0.45,
                "risk_class": "Moderate",
                "risk_color": "#F39C12",
                "class_label": "Prediabetes"
            }
        }
    )


class DiabetesPrediction(BaseModel):
    """Diabetes-specific prediction results."""
    
    probability: float = Field(..., ge=0, le=1, description="Diabetes probability")
    risk_class: str = Field(..., description="Risk class (Low/Moderate/High)")
    risk_color: str = Field(..., description="Color code for UI")
    class_label: str = Field(..., description="Detailed class (Normal/Prediabetes/Diabetic)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "probability": 0.45,
                "risk_class": "Moderate",
                "risk_color": "#F39C12",
                "class_label": "Prediabetes"
            }
        }
    )


class ObesityPrediction(BaseModel):
    """Obesity-specific prediction results (rule-based)."""
    
    bmi: float = Field(..., description="Calculated BMI")
    bmi_category: str = Field(..., description="BMI category")
    risk_class: str = Field(..., description="Risk class (Low/Moderate/High)")
    risk_color: str = Field(..., description="Color code for UI")
    obesity_class: str = Field(..., description="Obesity class (Normal/Overweight/Obese)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bmi": 24.65,
                "bmi_category": "Normal",
                "risk_class": "Low",
                "risk_color": "#2ECC71",
                "obesity_class": "Normal"
            }
        }
    )


class PredictionRequest(BaseModel):
    """Request model for running predictions."""
    
    patient_id: str = Field(..., description="Patient identifier")
    visit_id: Optional[str] = Field(None, description="Screening visit identifier (optional, will create if not provided)")
    # Optional because tests may provide only patient_id + visit_id.
    screening_data: Optional["ScreeningDataRequest"] = Field(None, description="Screening measurements")

    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "screening_data": {
                    "weight": 75.5,
                    "height": 1.75,
                    "physical_activity": True,
                    "family_history_diabetes": True,
                    "previous_gdm": False,
                    "has_hypertension": False,
                    "is_pregnant": False,
                    "residence": "Urban"
                }
            }
        }
    )


class PredictionResponse(BaseModel):
    """Response model for prediction results."""
    
    prediction_id: str = Field(..., description="Prediction identifier")
    visit_id: str = Field(..., description="Screening visit identifier")
    patient_id: str = Field(..., description="Patient identifier")
    diabetes: DiabetesPrediction = Field(..., description="Diabetes prediction")
    obesity: ObesityPrediction = Field(..., description="Obesity prediction")
    model_version: str = Field(..., description="Model version used")
    prediction_date: datetime = Field(..., description="Prediction timestamp")
    latency_ms: Optional[float] = Field(None, description="Prediction latency in milliseconds")

    # ── Explanations ──────────────────────────────────────────────────────────
    shap_explanation: Optional[SHAPExplanationResponse] = Field(None, description="SHAP explanation")
    lime_explanation: Optional[LIMEExplanationResponse] = Field(None, description="LIME explanation")
    global_feature_importance: Optional[GlobalFeatureImportanceResponse] = Field(None, description="Global feature importance")
    
    # ── Recommendation ──────────────────────────────────────────────────────
    recommendation: Optional["RecommendationResponse"] = Field(None, description="Clinical recommendation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prediction_id": "550e8400-e29b-41d4-a716-446655440003",
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "diabetes": {
                    "probability": 0.45,
                    "risk_class": "Moderate",
                    "risk_color": "#F39C12",
                    "class_label": "Prediabetes"
                },
                "obesity": {
                    "bmi": 24.65,
                    "bmi_category": "Normal",
                    "risk_class": "Low",
                    "risk_color": "#2ECC71",
                    "obesity_class": "Normal"
                },
                "model_version": "1.0.0",
                "prediction_date": "2024-01-15T10:30:00Z",
                "latency_ms": 125.5,
                "shap_explanation": {},
                "lime_explanation": {},
                "global_feature_importance": {},
                "recommendation": {}
            }
        }
    )

PredictionRequest.model_rebuild()
PredictionResponse.model_rebuild()