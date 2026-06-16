"""
Machine learning layer: model loading, feature preparation,
diabetes prediction, obesity assessment, and explainability.

Public API
----------
    model_loader              — singleton, populated at startup in main.py
    PatientFeatures            — input struct; use .from_screening_data() factory
    build_feature_row()        — raw fields → scaled DataFrame
    predict_diabetes()         — model output + Youden-J risk band
    assess_obesity()           — rule-based BMI → risk (no ML)
    explain_with_shap()        — per-patient SHAP (pre-fitted explainer)
    explain_with_lime()        — per-patient LIME (fitted per request)
    get_feature_importance()   — global native feature importance
    FeatureContribution        — TypedDict matching schemas/explanation.py
"""

from app.ml.diabetes_predictor import DiabetesPredictionResult, predict_diabetes
from app.ml.explainers import (
    FeatureContribution,
    explain_with_lime,
    explain_with_shap,
    get_feature_importance,
)
from app.ml.feature_builder import PatientFeatures, build_feature_row
from app.ml.model_loader import ModelLoader, model_loader
from app.ml.obesity import (
    assess_obesity,
    calculate_bmi,
    get_bmi_category,
    get_obesity_risk,
)

__all__ = [
    # Singleton
    "model_loader",
    "ModelLoader",
    # Feature building
    "PatientFeatures",
    "build_feature_row",
    # Predictions
    "predict_diabetes",
    "DiabetesPredictionResult",
    # Obesity (rule-based)
    "assess_obesity",
    "calculate_bmi",
    "get_bmi_category",
    "get_obesity_risk",
    # Explainability
    "explain_with_shap",
    "explain_with_lime",
    "get_feature_importance",
    "FeatureContribution",
]