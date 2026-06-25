"""
SHAP explanation schemas for model interpretability.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FeatureContribution(BaseModel):
    """Individual feature contribution to prediction."""
    
    feature_name: str = Field(..., description="Name of the feature")
    value: float = Field(..., description="Feature value (actual input)")
    shap_value: float = Field(..., description="SHAP contribution value")
    impact_direction: str = Field(..., description="Positive/Negative impact on risk")
    importance_abs: float = Field(..., description="Absolute importance for ranking")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature_name": "bmi",
                "value": 31.5,
                "shap_value": 0.12,
                "impact_direction": "Positive",
                "importance_abs": 0.12
            }
        }
    )


class SHAPExplanationResponse(BaseModel):
    """Response model for SHAP explanation."""
    
    explanation_id: str = Field(..., description="Explanation identifier")
    prediction_id: str = Field(..., description="Associated prediction identifier")
    base_value: float = Field(..., description="Base probability (population average)")
    final_probability: float = Field(..., description="Final predicted probability")
    feature_contributions: List[FeatureContribution] = Field(..., description="All feature contributions")
    top_positive_features: List[FeatureContribution] = Field(..., description="Top 5 risk-increasing features")
    top_negative_features: List[FeatureContribution] = Field(..., description="Top 5 risk-decreasing features")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "explanation_id": "550e8400-e29b-41d4-a716-446655440004",
                "prediction_id": "550e8400-e29b-41d4-a716-446655440003",
                "base_value": 0.15,
                "final_probability": 0.45,
                "feature_contributions": [],
                "top_positive_features": [],
                "top_negative_features": []
            }
        }
    )

class LIMEExplanationResponse(BaseModel):
    """Response model for LIME explanation."""
    
    explanation_id: str = Field(..., description="Explanation identifier")
    prediction_id: str = Field(..., description="Associated prediction identifier")
    feature_contributions: List[FeatureContribution] = Field(..., description="All feature contributions")
    top_positive_features: List[FeatureContribution] = Field(..., description="Top 5 risk-increasing features")
    top_negative_features: List[FeatureContribution] = Field(..., description="Top 5 risk-decreasing features")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "explanation_id": "550e8400-e29b-41d4-a716-446655440005",
                "prediction_id": "550e8400-e29b-41d4-a716-446655440003",
                "feature_contributions": [],
                "top_positive_features": [],
                "top_negative_features": []
            }
        }
    )



class GlobalFeatureImportanceResponse(BaseModel):
    """Response model for global feature importance."""
    
    model_version: str = Field(..., description="Model version")
    feature_importance: Dict[str, float] = Field(..., description="Feature name to importance score")
    sorted_features: List[str] = Field(..., description="Features sorted by importance (descending)")
    updated_at: str = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_version": "1.0.0",
                "feature_importance": {
                    "bmi": 0.25,
                    "age": 0.20,
                    "family_history_diabetes": 0.15
                },
                "sorted_features": ["bmi", "age", "family_history_diabetes"],
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )

class CombinedExplanationResponse(BaseModel):
    """Combined response model for all explanations."""
    
    prediction_id: str = Field(..., description="Associated prediction identifier")
    shap: Optional[SHAPExplanationResponse] = Field(None, description="SHAP explanation")
    lime: Optional[LIMEExplanationResponse] = Field(None, description="LIME explanation")
    global_feature_importance: Optional[GlobalFeatureImportanceResponse] = Field(None, description="Global feature importance")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prediction_id": "550e8400-e29b-41d4-a716-446655440003",
                "shap": {},
                "lime": {},
                "global_feature_importance": {}
            }
        }
    )