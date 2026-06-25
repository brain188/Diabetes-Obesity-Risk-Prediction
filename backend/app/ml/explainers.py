"""
Per-patient explainability: SHAP, LIME, and native feature importance.

Output types are aligned with schemas/explanation.py (FeatureContribution):
    feature_name     : str   (not "feature")
    value            : float (scaled [0,1] value for this patient)
    shap_value       : float (not "contribution")
    impact_direction : str   "Positive" | "Negative"  (not "increases_risk")
    importance_abs   : float abs(shap_value)

PredictionRepository.save_shap_explanation() expects:
    base_value              : float
    feature_contributions   : dict[str, float]   {feature_name: shap_value}
    top_positive_features   : list[dict]          (schema FeatureContribution shape)
    top_negative_features   : list[dict]
"""

from typing import TypedDict

import traceback

import numpy as np
import pandas as pd
import shap

from app.core.logging import get_logger
from app.ml.model_loader import ModelLoader
from lime.lime_tabular import LimeTabularExplainer

log = get_logger(__name__)

DIABETIC_CLASS_INDEX = 2
TOP_N_FACTORS = 5


# ── Shared output type

class FeatureContribution(TypedDict):
    feature_name    : str
    value           : float   # scaled [0,1] value for this patient
    shap_value      : float
    impact_direction: str     # "Positive" | "Negative"
    importance_abs  : float


# =============================================================================
# SHAP
# =============================================================================

def explain_with_shap(
    patient_features: pd.DataFrame,
    model_loader: ModelLoader,
) -> tuple[
    list[FeatureContribution],   # top_positive_features  (risk-increasing)
    list[FeatureContribution],   # top_negative_features  (risk-decreasing)
    float,                        # base_value
    dict[str, float],             # feature_contributions  (full flat dict for DB)
]:
    """
    Compute per-patient SHAP values for the Diabetic class.

    Uses the cached TreeExplainer from model_loader (built once at startup).
    Falls back to building a fresh one if the cache is unavailable.
    Handles both the old list-based API (SHAP < 0.42) and the new
    Explanation-object API.

    Returns
    -------
    (top_positive, top_negative, base_value, feature_contributions_dict)
    """
    feature_names = model_loader.feature_names

    # Use cached explainer — avoids rebuilding (~0.5–2 s) on every request
    try:
        explainer = model_loader.get_shap_explainer_cached()
    except Exception:
        log.warning("Cached SHAP explainer unavailable, building fresh one.")
        explainer = shap.TreeExplainer(model_loader.get_model())

    feature_values = patient_features.iloc[0].to_dict()

    # ── Compute SHAP values, handling old and new APIs ──────────────────────
    sv_diabetic: np.ndarray
    base_value: float

    try:
        # New API (SHAP >= 0.42): explainer(X) returns an Explanation object
        explanation = explainer(patient_features)
        sv_array    = np.asarray(explanation.values)   # (1, n_features) or (1, n_features, n_classes)
        bv_array    = np.asarray(explanation.base_values)

        if sv_array.ndim == 3:                          # multiclass
            sv_diabetic = sv_array[0, :, DIABETIC_CLASS_INDEX]
            base_value  = float(bv_array[0, DIABETIC_CLASS_INDEX]) if bv_array.ndim == 2 else float(bv_array[0])
        else:                                           # binary / single output
            sv_diabetic = sv_array[0]
            base_value  = float(bv_array[0]) if bv_array.ndim >= 1 else float(bv_array)

    except Exception:
        log.warning("New SHAP API failed, falling back to shap_values():\n%s", traceback.format_exc())
        # Old API: shap_values() returns list[ndarray] for multiclass or ndarray
        raw_shap = explainer.shap_values(patient_features)
        if isinstance(raw_shap, list):
            sv_diabetic = np.asarray(raw_shap[DIABETIC_CLASS_INDEX])[0]
            expected    = explainer.expected_value
            base_value  = (
                float(expected[DIABETIC_CLASS_INDEX])
                if hasattr(expected, "__len__")
                else float(expected)
            )
        else:
            sv_diabetic = np.asarray(raw_shap)[0]
            base_value  = float(explainer.expected_value)

    # ── Build output ─────────────────────────────────────────────────────────
    feature_contributions: dict[str, float] = {
        feat: round(float(sv), 6)
        for feat, sv in zip(feature_names, sv_diabetic)
    }

    all_contributions: list[FeatureContribution] = [
        {
            "feature_name"    : feat,
            "value"           : round(float(feature_values.get(feat, 0.0)), 4),
            "shap_value"      : round(float(sv), 6),
            "impact_direction": "Positive" if sv > 0 else "Negative",
            "importance_abs"  : round(abs(float(sv)), 6),
        }
        for feat, sv in zip(feature_names, sv_diabetic)
    ]

    all_contributions.sort(key=lambda c: c["importance_abs"], reverse=True)

    top_positive = [c for c in all_contributions if c["impact_direction"] == "Positive"][:TOP_N_FACTORS]
    top_negative = [c for c in all_contributions if c["impact_direction"] == "Negative"][:TOP_N_FACTORS]

    log.debug(
        "SHAP: %d risk factors, %d protective factors, base=%.4f",
        len(top_positive), len(top_negative), base_value,
    )

    return top_positive, top_negative, round(base_value, 6), feature_contributions


# =============================================================================
# LIME
# =============================================================================

def explain_with_lime(
    patient_features: pd.DataFrame,
    background_data: pd.DataFrame,
    model_loader: ModelLoader,
    num_samples: int = 200,
) -> list[FeatureContribution]:
    """
    Compute a LIME explanation for one patient for the Diabetic class.

    LIME is model-agnostic and fits a local linear surrogate by perturbing
    the input. It provides a complementary view to SHAP (FR-6.1 / FR-6.2).

    Parameters
    ----------
    patient_features : pd.DataFrame — single scaled row
    background_data  : pd.DataFrame — training distribution (for value ranges)
    model_loader      : ModelLoader
    num_samples       : int — perturbations to generate (200 gives good fidelity in ~0.3s)

    Returns
    -------
    list[FeatureContribution] — top TOP_N_FACTORS features, sorted by |shap_value|
    """

    model         = model_loader.get_model()
    feature_names = model_loader.feature_names

    # Use cached explainer — avoids rebuilding (~0.3–1 s) on every request
    try:
        explainer = model_loader.get_lime_explainer_cached()
    except Exception:
        log.warning("Cached LIME explainer unavailable, building fresh one.")
        explainer = LimeTabularExplainer(
            training_data=background_data.values,
            feature_names=feature_names,
            class_names=["Normal", "Prediabetes", "Diabetic"],
            mode="classification",
            discretize_continuous=True,
            random_state=42,
        )

    explanation = explainer.explain_instance(
        data_row  = patient_features.iloc[0].values,
        predict_fn= model.predict_proba,
        labels    = (DIABETIC_CLASS_INDEX,),
        num_features = len(feature_names),
        num_samples  = num_samples,
    )

    feature_values = patient_features.iloc[0].to_dict()

    contributions: list[FeatureContribution] = []
    for condition, weight in explanation.as_list(label=DIABETIC_CLASS_INDEX):
        feat = _extract_feature_name(condition, feature_names)
        contributions.append({
            "feature_name"    : feat,
            "value"           : round(float(feature_values.get(feat, 0.0)), 4),
            "shap_value"      : round(float(weight), 6),   # "shap_value" reused for LIME weight
            "impact_direction": "Positive" if weight > 0 else "Negative",
            "importance_abs"  : round(abs(float(weight)), 6),
        })

    contributions.sort(key=lambda c: c["importance_abs"], reverse=True)
    log.debug("LIME: %d feature conditions computed", len(contributions))
    return contributions[:TOP_N_FACTORS]


def _extract_feature_name(condition: str, feature_names: list[str]) -> str:
    """Extract the feature name from a LIME condition string like 'bmi > 0.65'."""
    for name in feature_names:
        if name in condition:
            return name
    return condition


# =============================================================================
# Native feature importance (global, identical for every patient)
# =============================================================================

def get_feature_importance(model_loader: ModelLoader) -> tuple[list[dict], str]:
    """
    Return the model's native feature importances, ranked descending.

    Global — same for every patient. Computed once per process start
    (FR-6.3 Global Feature Importance).

    Returns
    -------
    (ranked_list, method_description)

    ranked_list : list[{"feature": str, "importance": float, "rank": int}]
    method      : human-readable description (CatBoost / MDI / etc.)
    """
    model         = model_loader.get_model()
    feature_names = model_loader.feature_names

    if hasattr(model, "get_feature_importance"):
        importances = model.get_feature_importance()
        method      = "CatBoost gain-based importance (PredictionValuesChange)"
    elif hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        method      = "Mean Decrease in Impurity (MDI)"
    else:
        log.warning("Model has no native feature importance attribute.")
        return [], "Not available for this model type"

    ranked = sorted(
        zip(feature_names, importances),
        key=lambda pair: pair[1],
        reverse=True,
    )

    result = [
        {
            "feature"   : feat,
            "importance": round(float(imp), 6),
            "rank"      : rank + 1,
        }
        for rank, (feat, imp) in enumerate(ranked)
    ]

    log.debug("Feature importance computed (%d features, method=%s)", len(result), method)
    return result, method