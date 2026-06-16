"""
Builds the scaled, model-ready single-row DataFrame from ScreeningData.

Field names match ScreeningData ORM columns:
    weight              (kg)
    height              (m)
    bmi                 (pre-computed, stored on ScreeningData)
    bmi_category        "Normal"|"Overweight"|"Obese I"|"Obese II+"
    physical_activity   bool  → encoded as physically_active (0/1)
    age                 int, stored on ScreeningData at screening time
    sex                 str, from Patient.sex

Pipeline
--------
    PatientFeatures (raw DB values)
        ↓
    encode categoricals + booleans
        ↓
    order columns per model_metadata["feature_names"]
        ↓
    scaler.transform()   ← NEVER fit_transform
        ↓
    scaled 1-row DataFrame → model.predict_proba()
"""

import pandas as pd

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.ml.encoders import (
    encode_bmi_category,
    encode_boolean,
    encode_residence,
    encode_sex,
)
from app.ml.model_loader import ModelLoader

log = get_logger(__name__)


class PatientFeatures:
    """
    Raw screening fields for ONE patient.

    Field names match ScreeningData ORM columns so the prediction service
    can call PatientFeatures.from_screening_data() without manual remapping.

    Parameters
    ----------
    age                     : int  — ScreeningData.age
    sex                     : str  — "Male"|"Female" (from Patient.sex)
    is_pregnant             : bool — ScreeningData.is_pregnant
    bmi                     : float — ScreeningData.bmi (pre-computed)
    bmi_category            : str  — ScreeningData.bmi_category
    family_history_diabetes : bool
    previous_gdm            : bool
    physical_activity       : bool — ScreeningData.physical_activity
                                     encoded as physically_active (0/1)
    has_hypertension        : bool
    residence               : str  — "Urban"|"Rural"
    """

    def __init__(
        self,
        age: int,
        sex: str,
        is_pregnant: bool,
        bmi: float,
        bmi_category: str,
        family_history_diabetes: bool,
        previous_gdm: bool,
        physical_activity: bool,        # bool — matches ScreeningData column
        has_hypertension: bool,
        residence: str,
    ) -> None:
        self.age                     = age
        self.sex                     = sex
        self.is_pregnant             = is_pregnant
        self.bmi                     = bmi
        self.bmi_category            = bmi_category
        self.family_history_diabetes = family_history_diabetes
        self.previous_gdm            = previous_gdm
        self.physical_activity       = physical_activity
        self.has_hypertension        = has_hypertension
        self.residence               = residence

    @classmethod
    def from_screening_data(
        cls,
        screening_data,
        patient_sex: str,
    ) -> "PatientFeatures":
        """
        Build PatientFeatures directly from a ScreeningData ORM instance.

        Parameters
        ----------
        screening_data : ScreeningData ORM instance
        patient_sex    : str — from Patient.sex (not stored on ScreeningData)
        """
        return cls(
            age                     = screening_data.age,
            sex                     = patient_sex,
            is_pregnant             = screening_data.is_pregnant,
            bmi                     = screening_data.bmi,
            bmi_category            = screening_data.bmi_category,
            family_history_diabetes = screening_data.family_history_diabetes,
            previous_gdm            = screening_data.previous_gdm,
            physical_activity       = screening_data.physical_activity,  # bool
            has_hypertension        = screening_data.has_hypertension,
            residence               = screening_data.residence,
        )


def build_feature_row(
    patient: PatientFeatures,
    model_loader: ModelLoader,
) -> pd.DataFrame:
    """
    Convert raw screening fields to a scaled, model-ready single-row DataFrame.

    Steps
    -----
    1. Encode categoricals: sex, residence, bmi_category
    2. Encode all booleans via encode_boolean() — including physical_activity
       (bool) which maps to the model's "physically_active" feature name
    3. Order columns exactly as model_metadata["feature_names"]
    4. Apply fitted scaler.transform() — NEVER fit_transform

    Parameters
    ----------
    patient      : PatientFeatures
    model_loader : ModelLoader — provides feature_names + fitted scaler

    Returns
    -------
    pd.DataFrame — shape (1, n_features), values in [0, 1]

    Raises
    ------
    ValidationError — on unrecognised categorical values or missing features
    """
    # Encode all fields
    encoded: dict[str, float] = {
        "age"                    : float(patient.age),
        "sex"                    : encode_sex(patient.sex),
        "is_pregnant"            : encode_boolean(patient.is_pregnant),
        "bmi"                    : float(patient.bmi),
        "bmi_category"           : encode_bmi_category(patient.bmi_category),
        "family_history_diabetes": encode_boolean(patient.family_history_diabetes),
        "previous_gdm"           : encode_boolean(patient.previous_gdm),
        "physically_active"      : encode_boolean(patient.physical_activity),
        "has_hypertension"       : encode_boolean(patient.has_hypertension),
        "residence"              : encode_residence(patient.residence),
    }

    # Order columns per training
    feature_names = model_loader.feature_names

    missing = [f for f in feature_names if f not in encoded]
    if missing:
        raise ValidationError(
            f"Feature builder is missing required features: {missing}. "
            "PatientFeatures may be out of sync with model_metadata['feature_names']."
        )

    row    = {col: encoded[col] for col in feature_names}
    df_raw = pd.DataFrame([row], columns=feature_names)

    log.debug(
        "Pre-scaling features: %s",
        {k: round(v, 4) for k, v in row.items()},
    )

    # Apply fitted scaler
    scaler    = model_loader.get_scaler()
    df_scaled = pd.DataFrame(
        scaler.transform(df_raw),
        columns=feature_names,
    )

    log.debug(
        "Post-scaling features: %s",
        {k: round(v, 4) for k, v in df_scaled.iloc[0].to_dict().items()},
    )

    return df_scaled