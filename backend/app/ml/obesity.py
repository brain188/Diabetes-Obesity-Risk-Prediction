"""
Rule-based obesity assessment.

Uses WHO BMI thresholds — no machine learning model.
All field names match ScreeningData and the existing repositories:
    weight  (kg)  — ScreeningData.weight
    height  (m)   — ScreeningData.height
    bmi           — ScreeningData.bmi
    bmi_category  — "Normal"|"Overweight"|"Obese I"|"Obese II+"

Pipeline
--------
    weight (kg), height (m)
        ↓
    calculate_bmi()   → float
        ↓
    get_bmi_category() → "Normal"|"Overweight"|"Obese I"|"Obese II+"
        ↓
    get_obesity_risk() → "Low"|"Moderate"|"High"

obesity_probability is a rule-based confidence score (not from a model):
    Normal     (BMI <  25) → 0.10
    Overweight (BMI <  30) → 0.40
    Obese I    (BMI <  35) → 0.70
    Obese II+  (BMI >= 35) → 0.90
These values feed PredictionRepository.save_prediction(obesity_probability=...).
"""

from app.core.constants import (
    BMI_CAT_NORMAL,
    BMI_CAT_OBESE_I,
    BMI_CAT_OBESE_II,       # = "Obese II+"
    BMI_CAT_OVERWEIGHT,
    BMI_NORMAL_MAX,
    BMI_OBESE_I_MAX,
    BMI_OVERWEIGHT_MAX,
    RISK_HIGH,
    RISK_LOW,
    RISK_MODERATE,
)
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

log = get_logger(__name__)


def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate BMI from weight (kg) and height (m).

        BMI = weight / height²

    Field names match ScreeningData.weight and ScreeningData.height.

    Raises
    ------
    ValidationError — if height or weight is <= 0
    """
    if height <= 0:
        raise ValidationError("Height must be greater than zero.")
    if weight <= 0:
        raise ValidationError("Weight must be greater than zero.")
    return round(weight / (height ** 2), 2)


def get_bmi_category(bmi: float) -> str:
    """
    Map BMI to a WHO category string.
    Returns "Obese II+" (with +) to match ScreeningData.bmi_category.
    """
    if bmi < BMI_NORMAL_MAX:
        return BMI_CAT_NORMAL         # "Normal"
    if bmi < BMI_OVERWEIGHT_MAX:
        return BMI_CAT_OVERWEIGHT     # "Overweight"
    if bmi < BMI_OBESE_I_MAX:
        return BMI_CAT_OBESE_I        # "Obese I"
    return BMI_CAT_OBESE_II           # "Obese II+"


def get_obesity_risk(bmi: float) -> str:
    """Map BMI directly to a risk band."""
    if bmi < BMI_NORMAL_MAX:
        return RISK_LOW
    if bmi < BMI_OVERWEIGHT_MAX:
        return RISK_MODERATE
    return RISK_HIGH


def _get_obesity_probability(bmi: float) -> float:
    """
    Rule-based confidence score for obesity.
    Used to populate the obesity_probability column in Prediction.
    Not a model output — a deterministic mapping from BMI bucket.
    """
    if bmi < BMI_NORMAL_MAX:
        return 0.10
    if bmi < BMI_OVERWEIGHT_MAX:
        return 0.40
    if bmi < BMI_OBESE_I_MAX:
        return 0.70
    return 0.90


def assess_obesity(weight: float, height: float) -> dict:
    """
    Full obesity assessment from raw weight and height.

    Single entry point used by the prediction service.
    Returns all fields needed by PredictionRepository.save_prediction()
    and the Prediction ORM model.

    Parameters
    ----------
    weight : float — kg  (ScreeningData.weight field name)
    height : float — m   (ScreeningData.height field name)

    Returns
    -------
    dict with keys:
        bmi              : float  — e.g. 31.14
        bmi_category     : str    — "Normal"|"Overweight"|"Obese I"|"Obese II+"
        risk_class       : str    — "Low"|"Moderate"|"High"
        obesity_class    : str    — "Normal"|"Overweight"|"Obese" (for PredictionRepo)
        obesity_probability: float — rule-based score 0.10/0.40/0.70/0.90

    Example
    -------
    >>> assess_obesity(weight=90, height=1.70)
    {
        'bmi': 31.14,
        'bmi_category': 'Obese I',
        'risk_class': 'High',
        'obesity_class': 'Obese',
        'obesity_probability': 0.70
    }
    """
    bmi          = calculate_bmi(weight, height)
    bmi_category = get_bmi_category(bmi)
    risk_class   = get_obesity_risk(bmi)

    # obesity_class is the simplified label used in PredictionRepository
    # and Prediction.obesity_bmi_category (Normal / Overweight / Obese)
    if bmi_category == BMI_CAT_NORMAL:
        obesity_class = "Normal"
    elif bmi_category == BMI_CAT_OVERWEIGHT:
        obesity_class = "Overweight"
    else:
        obesity_class = "Obese"   # Covers Obese I and Obese II+

    probability = _get_obesity_probability(bmi)

    log.debug(
        "Obesity assessed: weight=%.1fkg height=%.2fm → "
        "bmi=%.2f category=%s risk=%s",
        weight, height, bmi, bmi_category, risk_class,
    )

    return {
        "bmi"                : bmi,
        "bmi_category"       : bmi_category,
        "risk_class"         : risk_class,
        "obesity_class"      : obesity_class,
        "obesity_probability": probability,
    }