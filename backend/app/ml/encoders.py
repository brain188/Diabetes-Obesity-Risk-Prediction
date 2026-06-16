"""
Categorical encoding maps — must mirror data_processing.yml exactly.

"""

from typing import Union

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

log = get_logger(__name__)


# Encoding maps

SEX_MAP: dict[str, int] = {
    "female": 0,
    "male"  : 1,
}

RESIDENCE_MAP: dict[str, int] = {
    "rural": 0,
    "urban": 1,
}

# "Obese II+" with the plus sign — matches ScreeningData.bmi_category and
# the Kedro training pipeline (bmi_map key "obese ii+").
BMI_CATEGORY_MAP: dict[str, int] = {
    "normal"    : 0,
    "overweight": 1,
    "obese i"   : 2,
    "obese ii+" : 3,
    "obese ii"  : 3,   # Defensive alias — accept without "+" too
}

_BOOL_TRUTHY = {"true", "1", "yes", "y"}


def encode_sex(sex: str) -> int:
    """
    Encode sex to 0 (female) or 1 (male).
    Raises ValidationError for unrecognised values.
    """
    key = sex.strip().lower()
    if key not in SEX_MAP:
        raise ValidationError(
            f"Invalid sex '{sex}'. Expected 'Male' or 'Female'."
        )
    return SEX_MAP[key]


def encode_residence(residence: str) -> int:
    """
    Encode residence to 0 (rural) or 1 (urban).
    Raises ValidationError for unrecognised values.
    """
    key = residence.strip().lower()
    if key not in RESIDENCE_MAP:
        raise ValidationError(
            f"Invalid residence '{residence}'. Expected 'Urban' or 'Rural'."
        )
    return RESIDENCE_MAP[key]


def encode_bmi_category(bmi_category: str) -> int:
    """
    Encode BMI category to its ordinal integer.
    Accepts "Obese II+" (DB value) and "Obese II" (defensive alias).
    """
    key = bmi_category.strip().lower()
    if key not in BMI_CATEGORY_MAP:
        raise ValidationError(
            f"Invalid bmi_category '{bmi_category}'. "
            "Expected: Normal | Overweight | Obese I | Obese II+"
        )
    return BMI_CATEGORY_MAP[key]


def encode_boolean(value: Union[bool, str, int]) -> int:
    """
    Encode any boolean-like value to 0/1.

    Used for ALL boolean fields:
        is_pregnant, family_history_diabetes, previous_gdm,
        physical_activity (bool), has_hypertension

    Accepts: True/False, "true"/"false", "1"/"0", "yes"/"no", 1/0.
    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if value else 0
    return 1 if str(value).strip().lower() in _BOOL_TRUTHY else 0