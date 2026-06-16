from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import shap

log = logging.getLogger(__name__)



MEDICAL_RANGES: dict[str, tuple[float, float]] = {
    "age" : (18,  100),   # years
    "bmi" : (10,  80),    # kg/m²
}

# Boolean columns — valid raw values (case-insensitive)
BOOL_TRUTHY  = {"true",  "1", "yes"}
BOOL_FALSY   = {"false", "0", "no"}

# Categorical allowed values (after lowercasing)
ALLOWED_SEX       = {"male", "female"}
ALLOWED_RESIDENCE = {"urban", "rural"}
ALLOWED_BMI_CAT   = {"normal", "overweight", "obese i", "obese ii+"}  # matches BMI_CAT_OBESE_II in constants.py

# Target class integer → string label
TARGET_LABELS = {0: "Normal", 1: "Prediabetes", 2: "Diabetic"}


def validate_patient_input(
    raw_patient: dict[str, Any],
    feature_names: list[str],
) -> dict[str, Any]:
    """
    Validate and lightly normalise a raw patient input dictionary.

    Parameters
    ----------
    raw_patient  : dict — raw key/value pairs from the API request body
    feature_names: list — the feature columns the model was trained on,
                          loaded from model_metadata["feature_names"]

    Returns
    -------
    dict[str, Any]
        The same dict with string values lightly stripped and lowercased
        for categorical fields.

    Raises
    ------
    ValueError
        With a descriptive message for every validation failure found.
        All failures are collected before raising so the caller sees the
        full list at once.
    """
    errors: list[str] = []
    patient = {}

    REQUIRED_FIELDS = set(feature_names)

    for field in REQUIRED_FIELDS:
        if field not in raw_patient:
            errors.append(f"Required field '{field}' is missing.")

    if errors:
        raise ValueError(
            "Patient input validation failed — missing fields:\n  "
            + "\n  ".join(errors)
        )

    # Numerical range validation
    for col, (lo, hi) in MEDICAL_RANGES.items():
        if col not in raw_patient:
            continue
        try:
            val = float(raw_patient[col])
        except (TypeError, ValueError):
            errors.append(f"'{col}' must be a number, got: {raw_patient[col]!r}")
            continue
        if not (lo <= val <= hi):
            errors.append(
                f"'{col}' value {val} is outside valid range [{lo}, {hi}]."
            )
        patient[col] = val

    # Categorical field validation
    for col, allowed in [
        ("sex",          ALLOWED_SEX),
        ("bmi_category", ALLOWED_BMI_CAT),
        ("residence",    ALLOWED_RESIDENCE),
    ]:
        if col not in raw_patient:
            errors.append(f"Required categorical field '{col}' is missing.")
            continue
        val = str(raw_patient[col]).strip().lower()
        if val not in allowed:
            errors.append(
                f"'{col}' value '{val}' is not recognised. "
                f"Allowed values: {sorted(allowed)}"
            )
        patient[col] = val

    # Boolean field validation
    BOOL_FIELDS = [
        "is_pregnant", "family_history_diabetes",
        "previous_gdm", "physically_active", "has_hypertension",
    ]
    for col in BOOL_FIELDS:
        if col not in raw_patient:
            errors.append(f"Required boolean field '{col}' is missing.")
            continue
        raw_val = str(raw_patient[col]).strip().lower()
        if raw_val in BOOL_TRUTHY:
            patient[col] = 1
        elif raw_val in BOOL_FALSY:
            patient[col] = 0
        else:
            errors.append(
                f"'{col}' value '{raw_val}' is not a valid boolean. "
                "Use true/false, 1/0, or yes/no."
            )

    # Copy age separately
    if "age" in raw_patient and "age" not in patient:
        try:
            patient["age"] = int(float(raw_patient["age"]))
        except (TypeError, ValueError):
            errors.append(f"'age' must be a number, got: {raw_patient['age']!r}")

    if errors:
        raise ValueError(
            "Patient input validation failed:\n  " + "\n  ".join(errors)
        )

    log.info("Patient input validated successfully. Fields: %s", list(patient.keys()))
    return patient



def preprocess_patient_input(
    validated_patient: dict[str, Any],
    scaler: Any,
    model_metadata: dict[str, Any],
) -> pd.DataFrame:
    """
    Encode, order, and scale the validated patient dict into a single-row
    feature DataFrame ready for the model.

    Parameters
    ----------
    validated_patient : dict — output of ``validate_patient_input``
    scaler            : fitted MinMaxScaler from data/06_models/scaler.pkl
    model_metadata    : dict from data/08_reporting/model_metadata.json,
                        provides "feature_names" for column ordering

    Returns
    -------
    pd.DataFrame — shape (1, n_features), scaled to [0, 1]
    """
    SEX_MAP       = {"female": 0, "male": 1}
    BMI_CAT_MAP   = {"normal": 0, "overweight": 1, "obese i": 2, "obese ii+": 3}  # must stay in sync with constants.BMI_CAT_OBESE_II
    RESIDENCE_MAP = {"rural": 0, "urban": 1}

    # Apply categorical encodings
    encoded = dict(validated_patient)   # shallow copy

    encoded["sex"]          = SEX_MAP.get(str(encoded.get("sex", "")).lower(), 0)
    encoded["bmi_category"] = BMI_CAT_MAP.get(str(encoded.get("bmi_category", "")).lower(), 0)
    encoded["residence"]    = RESIDENCE_MAP.get(str(encoded.get("residence", "")).lower(), 0)

    # Build ordered DataFrame using feature_names from metadata
    feature_names = model_metadata.get("feature_names", [])

    if not feature_names:
        raise ValueError(
            "model_metadata['feature_names'] is empty. "
            "Ensure the training pipeline completed successfully."
        )

    row = {}
    for col in feature_names:
        row[col] = encoded.get(col, np.nan)  # NaN for missing optional columns

    df_raw = pd.DataFrame([row], columns=feature_names)

    log.info("Pre-scaling feature row:\n%s", df_raw.to_string())

    # Apply fitted scaler
    # .transform() only — never .fit_transform() at inference time
    df_scaled = pd.DataFrame(
        scaler.transform(df_raw),
        columns = feature_names,
    )

    log.info("Post-scaling feature row:\n%s", df_scaled.to_string())
    return df_scaled



def run_prediction(
    trained_model: Any,
    patient_features: pd.DataFrame,
) -> dict[str, Any]:
    """
    Run the trained model on the preprocessed patient feature row.

    Returns both the predicted class index and the full probability
    distribution across all three classes so that the risk band classifier
    and SHAP explainer can use them.

    Parameters
    ----------
    trained_model    : fitted estimator from data/06_models/trained_model.pkl
    patient_features : scaled single-row DataFrame from preprocess_patient_input

    Returns
    -------
    dict with keys:
        ``predicted_class``  — int  (0, 1, or 2)
        ``predicted_label``  — str  ("Normal", "Prediabetes", or "Diabetic")
        ``probabilities``    — dict {class_label: probability}
        ``prob_array``       — np.ndarray shape (3,) — needed by classify_risk_band
    """
    prob_array      = trained_model.predict_proba(patient_features)[0]   # shape (3,)
    predicted_class = int(np.argmax(prob_array))
    predicted_label = TARGET_LABELS[predicted_class]

    probabilities = {
        TARGET_LABELS[i]: round(float(p), 6)
        for i, p in enumerate(prob_array)
    }

    log.info("Prediction:")
    log.info("  Predicted class  : %d (%s)", predicted_class, predicted_label)
    for label, prob in probabilities.items():
        log.info("  P(%-12s) : %.4f", label, prob)

    return {
        "predicted_class" : predicted_class,
        "predicted_label" : predicted_label,
        "probabilities"   : probabilities,
        "prob_array"      : prob_array,
    }



def classify_risk_band(
    prediction_output: dict[str, Any],
    model_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Assign a clinical risk band based on P(Diabetic) and the Youden-J
    optimal threshold computed during the training pipeline.

    Risk bands
    ----------
    Low      : P(Diabetic) < thresh_low_high
    Moderate : thresh_low_high <= P(Diabetic) < thresh_high
    High     : P(Diabetic) >= thresh_high

    The thresholds are loaded from model_metadata["threshold"] where they
    were saved by the training pipeline's evaluate_final_model node.

    Parameters
    ----------
    prediction_output : dict — output of ``run_prediction``
    model_metadata    : dict — contains "threshold" from evaluate_final_model

    Returns
    -------
    dict with keys:
        ``risk_band``       — "Low", "Moderate", or "High"
        ``risk_color``      — hex color code for frontend display
        ``p_diabetic``      — float probability of Diabetic class
        ``opt_threshold``   — float threshold used for classification
        ``risk_description``— str human-readable explanation of the band
    """
    threshold_info  = model_metadata.get("threshold", {})
    thresh_low_high = float(threshold_info.get("thresh_low_high", 0.50))
    thresh_high     = float(threshold_info.get("thresh_high",     0.70))

    prob_array  = prediction_output["prob_array"]
    p_diabetic  = float(prob_array[2])   # P(class 2 = Diabetic)

    # Assign risk band
    if p_diabetic >= thresh_high:
        risk_band   = "High"
        risk_color  = "#E74C3C"   # Red
        description = (
            f"P(Diabetic) = {p_diabetic:.3f} ≥ {thresh_high:.3f}. "
            "Urgent referral to physician recommended. "
        )
    elif p_diabetic >= thresh_low_high:
        risk_band   = "Moderate"
        risk_color  = "#F39C12"   # Amber
        description = (
            f"P(Diabetic) = {p_diabetic:.3f} ≥ {thresh_low_high:.3f}. "
            "Lifestyle counselling recommended. "
            "Repeat screening in 3 months."
        )
    else:
        risk_band   = "Low"
        risk_color  = "#2ECC71"   # Green
        description = (
            f"P(Diabetic) = {p_diabetic:.3f} < {thresh_low_high:.3f}. "
            "No immediate intervention required. "
            "Routine annual screening advised."
        )

    log.info(
        "Risk band: %s  (P(Diabetic)=%.4f, thresh_low=%.4f, thresh_high=%.4f)",
        risk_band, p_diabetic, thresh_low_high, thresh_high,
    )

    return {
        "risk_band"       : risk_band,
        "risk_color"      : risk_color,
        "p_diabetic"      : round(p_diabetic, 6),
        "opt_threshold"   : round(thresh_low_high, 6),
        "risk_description": description,
    }




def explain_prediction(
    shap_explainer: Any,
    patient_features: pd.DataFrame,
    model_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute a per-patient SHAP explanation for the Diabetic class.

    Returns the top contributing features (both risk-increasing and
    risk-decreasing) so the FastAPI response can display a human-readable
    explanation of why the patient received their risk score.

    Parameters
    ----------
    shap_explainer   : fitted SHAP explainer from data/06_models/shap_explainer.pkl
    patient_features : scaled single-row DataFrame (same input used for prediction)
    model_metadata   : dict — provides "feature_names" and "target_encoding"

    Returns
    -------
    dict with keys:
        ``shap_values_diabetic`` — list of {feature, value, shap, direction}
                                   for the Diabetic class, sorted by |SHAP|
        ``top_risk_factors``     — top 5 features increasing Diabetic risk
        ``top_protective_factors``— top 3 features decreasing Diabetic risk
        ``base_value``           — model's average prediction (SHAP base value)
    """
    feature_names = model_metadata.get("feature_names", patient_features.columns.tolist())

    # Compute SHAP values
    raw_shap = shap_explainer.shap_values(patient_features)

    # For multiclass: raw_shap is a list of arrays, one per class
    # Index 2 = Diabetic class
    if isinstance(raw_shap, list):
        sv_diabetic = np.array(raw_shap[2])[0]          # shape (n_features,)
        base_val    = (
            shap_explainer.expected_value[2]
            if hasattr(shap_explainer.expected_value, "__len__")
            else float(shap_explainer.expected_value)
        )
    else:
        sv_diabetic = np.array(raw_shap)[0]
        base_val    = float(shap_explainer.expected_value)

    # Build ranked explanation list
    feature_values = patient_features.iloc[0].to_dict()
    explanations   = []

    for feat, sv in zip(feature_names, sv_diabetic):
        explanations.append({
            "feature"  : feat,
            "value"    : round(float(feature_values.get(feat, np.nan)), 4),
            "shap"     : round(float(sv), 6),
            "direction": "increases_risk" if sv > 0 else "decreases_risk",
        })

    # Sort by absolute SHAP value descending
    explanations.sort(key=lambda x: abs(x["shap"]), reverse=True)

    top_risk_factors      = [e for e in explanations if e["direction"] == "increases_risk"][:5]
    top_protective_factors= [e for e in explanations if e["direction"] == "decreases_risk"][:3]

    log.info("SHAP explanation (Diabetic class, top 5 features):")
    for e in explanations[:5]:
        log.info(
            "  %-30s : SHAP=%.4f  value=%.4f  (%s)",
            e["feature"], e["shap"], e["value"], e["direction"],
        )

    return {
        "shap_values_diabetic"  : explanations,
        "top_risk_factors"      : top_risk_factors,
        "top_protective_factors": top_protective_factors,
        "base_value"            : round(float(base_val), 6),
    }


def explain_prediction_lime(
    trained_model: Any,
    patient_features: pd.DataFrame,
    X_train: pd.DataFrame,
    model_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate a LIME explanation for a single patient prediction.

    LIME fits a local linear model around this specific patient's data point
    to explain which features pushed the prediction in the observed direction.

    WHY LIME at inference time alongside SHAP?
    ------------------------------------------
    SHAP provides theoretically grounded additive feature attributions.
    LIME provides a simpler local linear approximation that is often easier
    to communicate to non-technical healthcare workers ("if your BMI were
    lower, your risk score would drop by X").

    Serving both gives the frontend two complementary explanation views.

    Parameters
    ----------
    trained_model    : fitted estimator
    patient_features : scaled single-row DataFrame (same used for SHAP)
    X_train          : training features — LIME uses these as the background
    model_metadata   : provides feature_names and target_encoding

    Returns
    -------
    dict with keys:
        ``lime_explanation``  — list of {feature, weight, direction} dicts
                                sorted by |weight| descending
        ``predicted_label``   — string label for the class being explained
    """
    from lime import lime_tabular

    feature_names = model_metadata.get("feature_names", patient_features.columns.tolist())

    explainer = lime_tabular.LimeTabularExplainer(
        training_data = X_train.values,
        feature_names = feature_names,
        class_names   = ["Normal", "Prediabetes", "Diabetic"],
        mode          = "classification",
        random_state  = 42,
    )

    # Explain toward the Diabetic class (class index 2) — most clinically relevant
    lime_exp = explainer.explain_instance(
        data_row     = patient_features.values[0],
        predict_fn   = trained_model.predict_proba,
        num_features = min(10, len(feature_names)),
        num_samples  = 500,
        labels       = (2,),
    )

    raw_explanation = lime_exp.as_list(label=2)

    explanation = [
        {
            "feature"  : item[0],
            "weight"   : round(float(item[1]), 6),
            "direction": "increases_risk" if item[1] > 0 else "decreases_risk",
        }
        for item in sorted(raw_explanation, key=lambda x: abs(x[1]), reverse=True)
    ]

    log.info("LIME explanation (Diabetic class, top features):")
    for e in explanation[:5]:
        log.info("  %-30s : %.4f  (%s)", e["feature"], e["weight"], e["direction"])

    return {
        "lime_explanation": explanation,
        "predicted_label" : "Diabetic",
    }


def get_feature_importance(
    trained_model: Any,
    model_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Return the model's native feature importances as a ranked list.

    This is model-specific importance (gain-based for CatBoost/XGBoost,
    MDI for Random Forest) — different from SHAP importance but useful
    as a complementary view.

    Parameters
    ----------
    trained_model  : fitted estimator
    model_metadata : provides feature_names

    Returns
    -------
    dict with keys:
        ``feature_importance`` — list of {feature, importance, rank} dicts
                                 sorted by importance descending
        ``method``             — string describing how importance was computed
    """
    feature_names = model_metadata.get("feature_names", [])

    if hasattr(trained_model, "get_feature_importance"):
        # CatBoost
        importances = trained_model.get_feature_importance()
        method      = "CatBoost gain-based importance"
    elif hasattr(trained_model, "feature_importances_"):
        # XGBoost, LightGBM, RandomForest
        importances = trained_model.feature_importances_
        method      = "Mean Decrease in Impurity (MDI)"
    else:
        log.warning("Model has no native feature importance attribute.")
        return {
            "feature_importance": [],
            "method"            : "Not available for this model type",
        }

    ranked = sorted(
        [
            {
                "feature"   : feat,
                "importance": round(float(imp), 6),
                "rank"      : rank + 1,
            }
            for rank, (feat, imp) in enumerate(
                sorted(zip(feature_names, importances),
                       key=lambda x: x[1], reverse=True)
            )
        ],
        key=lambda x: x["rank"],
    )

    log.info("Feature importance (%s):", method)
    for item in ranked[:5]:
        log.info("  #%d  %-30s : %.4f", item["rank"], item["feature"], item["importance"])

    return {
        "feature_importance": ranked,
        "method"            : method,
    }



def build_prediction_response(
    validated_patient: dict[str, Any],
    prediction_output: dict[str, Any],
    risk_band_output: dict[str, Any],
    explanation_output: dict[str, Any],
    lime_explanation_output: dict[str, Any],
    feature_importance_output: dict[str, Any],
) -> dict[str, Any]:
    """
    Assemble the complete prediction response that the FastAPI endpoint
    returns to the frontend.

    The response contains everything the healthcare worker needs to:
        1.  Understand the risk level at a glance (risk_band + color)
        2.  See the probability breakdown across all three classes
        3.  Understand WHY this patient received this score (SHAP explanation)
        4.  Know what clinical action to take (risk_description)

    Parameters
    ----------
    validated_patient  : raw patient data (for echoing back to the caller)
    prediction_output  : output of ``run_prediction``
    risk_band_output   : output of ``classify_risk_band``
    explanation_output : output of ``explain_prediction``

    Returns
    -------
    dict[str, Any]
        The complete prediction response JSON.
    """

    clean_probabilities = prediction_output["probabilities"]

    response = {
        # Core prediction result
        "predicted_class"  : prediction_output["predicted_class"],
        "predicted_label"  : prediction_output["predicted_label"],
        "probabilities"    : clean_probabilities,

        # Risk band
        "risk_band"        : risk_band_output["risk_band"],
        "risk_color"       : risk_band_output["risk_color"],
        "p_diabetic"       : risk_band_output["p_diabetic"],
        "risk_description" : risk_band_output["risk_description"],
        "opt_threshold"    : risk_band_output["opt_threshold"],

        # SHAP explanation
        "top_risk_factors"       : explanation_output["top_risk_factors"],
        "top_protective_factors" : explanation_output["top_protective_factors"],
        "shap_base_value"        : explanation_output["base_value"],

        # LIME explanation
        "lime_explanation" : lime_explanation_output["lime_explanation"],

        # Native Feature Importance
        "feature_importance"        : feature_importance_output["feature_importance"],
        "feature_importance_method" : feature_importance_output["method"],

        # Echo patient input back for the frontend display
        "patient_input"    : {
            k: v for k, v in validated_patient.items()
            if k not in ("prob_array",)   # Never echo numpy arrays
        },
    }

    log.info("Prediction response assembled.")
    log.info("  Predicted  : %s", response["predicted_label"])
    log.info("  Risk band  : %s", response["risk_band"])
    log.info("  P(Diabetic): %.4f", response["p_diabetic"])

    return response
