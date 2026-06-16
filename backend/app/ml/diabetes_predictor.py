"""
Runs the trained CatBoost model and applies the Youden-J threshold to
produce a clinical risk band (Low / Moderate / High).

Output field names match PredictionRepository.save_prediction():
    diabetes_probability → float  (P(Diabetic))
    diabetes_risk_class  → str    "Low"|"Moderate"|"High"
    diabetes_class       → str    "Normal"|"Prediabetes"|"Diabetic"
"""

from typing import TypedDict

import numpy as np
import pandas as pd

from app.core.constants import RISK_HIGH, RISK_LOW, RISK_MODERATE
from app.core.exceptions import PredictionError
from app.core.logging import get_logger
from app.ml.model_loader import ModelLoader

log = get_logger(__name__)


class DiabetesPredictionResult(TypedDict):
    predicted_class    : int           # 0, 1, or 2 (argmax of predict_proba)
    predicted_label    : str           # "Normal" | "Prediabetes" | "Diabetic"
    probabilities      : dict[str, float]  # all three class probabilities
    diabetes_probability: float        # P(class == 2) — used for risk banding
    diabetes_risk_class : str          # "Low" | "Moderate" | "High"
    diabetes_class      : str          # same as predicted_label (repo field name)
    opt_threshold       : float        # thresh_low_high
    model_version       : str


def predict_diabetes(
    patient_features: pd.DataFrame,
    model_loader: ModelLoader,
) -> DiabetesPredictionResult:
    """
    Run the trained model on a scaled feature row and classify into a risk band.

    Parameters
    ----------
    patient_features : pd.DataFrame — single scaled row from build_feature_row()
    model_loader      : ModelLoader

    Returns
    -------
    DiabetesPredictionResult — all fields match PredictionRepository field names

    Raises
    ------
    PredictionError — if predict_proba fails
    """
    model          = model_loader.get_model()
    metadata       = model_loader.get_metadata()
    target_encoding: dict[str, str] = metadata["target_encoding"]  # {"0": "Normal", ...}
    threshold      = metadata["threshold"]

    try:
        prob_array = model.predict_proba(patient_features)[0]   # shape (3,)
    except Exception as exc:
        log.error("Model predict_proba failed: %s", exc)
        raise PredictionError(f"Diabetes model prediction failed: {exc}") from exc

    predicted_class = int(np.argmax(prob_array))
    predicted_label = target_encoding[str(predicted_class)]

    probabilities = {
        target_encoding[str(i)]: round(float(p), 6)
        for i, p in enumerate(prob_array)
    }

    # P(Diabetic) — used for Youden-J risk banding
    diabetes_probability = float(prob_array[2])

    thresh_low_high = float(threshold["thresh_low_high"])
    thresh_high     = float(threshold["thresh_high"])

    if diabetes_probability >= thresh_high:
        diabetes_risk_class = RISK_HIGH
    elif diabetes_probability >= thresh_low_high:
        diabetes_risk_class = RISK_MODERATE
    else:
        diabetes_risk_class = RISK_LOW

    log.info(
        "Diabetes prediction: label=%s p_diabetic=%.4f risk=%s "
        "(thresh_low=%.4f thresh_high=%.4f)",
        predicted_label, diabetes_probability,
        diabetes_risk_class, thresh_low_high, thresh_high,
    )

    return DiabetesPredictionResult(
        predicted_class     = predicted_class,
        predicted_label     = predicted_label,
        probabilities       = probabilities,
        diabetes_probability= round(diabetes_probability, 6),
        diabetes_risk_class = diabetes_risk_class,
        diabetes_class      = predicted_label,   # alias — matches save_prediction param
        opt_threshold       = round(thresh_low_high, 6),
        model_version       = model_loader.model_version,
    )