from __future__ import annotations

import logging
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from lime import lime_tabular
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

log = logging.getLogger(__name__)

# Class names used in every plot and report
CLASS_NAMES = ["Normal", "Prediabetes", "Diabetic"]


def _to_1d(y: pd.DataFrame | pd.Series | np.ndarray) -> np.ndarray:
    """
    Convert any target representation to a flat 1-D numpy array.

    The feature_engineering pipeline saves y as a single-column DataFrame
    so Parquet serialisation works.  All sklearn metrics require a 1-D array.

    Parameters
    ----------
    y : pd.DataFrame, pd.Series, or np.ndarray

    Returns
    -------
    np.ndarray — shape (n,), dtype int
    """
    if isinstance(y, pd.DataFrame):
        return y.iloc[:, 0].to_numpy(dtype=int)
    if isinstance(y, pd.Series):
        return y.to_numpy(dtype=int)
    return np.asarray(y, dtype=int).ravel()


def compute_test_metrics(
    trained_model: Any,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> dict[str, Any]:
    """
    Compute the full metric suite and per-class classification report on
    the held-out test set.

    Metrics computed
    ----------------
    accuracy        — overall fraction of correct predictions
    f1_macro        — unweighted mean F1 across all 3 classes; the primary
                      metric because it treats every class equally
    f1_weighted     — frequency-weighted mean F1 (secondary view)
    precision_macro — unweighted mean precision across all 3 classes
    recall_macro    — unweighted mean recall; minimises missed patients
    roc_auc_ovr     — one-vs-rest macro AUC; overall discriminative ability

    Parameters
    ----------
    trained_model : fitted estimator from data/06_models/trained_model.pkl
    X_test        : scaled test feature matrix (data/03_primary/X_test.parquet)
    y_test        : test target as single-column DataFrame

    Returns
    -------
    dict with keys:
        ``summary_metrics``       — dict of scalar float metrics
        ``classification_report`` — per-class precision/recall/F1/support dict
    """
    y_1d        = _to_1d(y_test)
    y_pred      = trained_model.predict(X_test)
    y_pred_prob = trained_model.predict_proba(X_test)

    summary_metrics = {
        "accuracy"       : round(float(accuracy_score(y_1d, y_pred)),                                      4),
        "f1_macro"       : round(float(f1_score(y_1d, y_pred,        average="macro",   zero_division=0)), 4),
        "f1_weighted"    : round(float(f1_score(y_1d, y_pred,        average="weighted",zero_division=0)), 4),
        "precision_macro": round(float(precision_score(y_1d, y_pred, average="macro",   zero_division=0)), 4),
        "recall_macro"   : round(float(recall_score(y_1d, y_pred,    average="macro",   zero_division=0)), 4),
        "roc_auc_ovr"    : round(float(roc_auc_score(
            y_1d, y_pred_prob, multi_class="ovr", average="macro"
        )), 4),
    }

    cls_report = classification_report(
        y_1d, y_pred,
        target_names = CLASS_NAMES,
        output_dict  = True,
    )

    # Log summary to Kedro output for the audit trail
    log.info("=== TEST SET METRICS ===")
    for name, value in summary_metrics.items():
        log.info("  %-20s : %.4f", name, value)

    log.info(
        "Classification report (test set):\n%s",
        classification_report(y_1d, y_pred, target_names=CLASS_NAMES),
    )

    return {
        "summary_metrics"      : summary_metrics,
        "classification_report": cls_report,
    }



def plot_confusion_matrix(
    trained_model: Any,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> str:
    """
    Generate and return a confusion matrix figure as PNG bytes.
    Two panels are produced side-by-side:
        Left  — raw prediction counts
        Right — row-normalised proportions (per-class recall at a glance)

    Parameters
    ----------
    trained_model : fitted estimator
    X_test        : test feature matrix
    y_test        : test target (single-column DataFrame)

    Returns
    -------
    bytes — PNG image bytes
    """
    y_1d   = _to_1d(y_test)
    y_pred = trained_model.predict(X_test)

    cm      = confusion_matrix(y_1d, y_pred)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Confusion Matrix — Test Set", fontsize=14, fontweight="bold")

    # Left panel: raw counts
    ConfusionMatrixDisplay(
        confusion_matrix = cm,
        display_labels   = CLASS_NAMES,
    ).plot(ax=axes[0], cmap="Blues", colorbar=False)
    axes[0].set_title("Raw Counts", fontweight="bold")
    axes[0].set_xlabel("Predicted Label")
    axes[0].set_ylabel("True Label")

    # Right panel: normalised proportions
    ConfusionMatrixDisplay(
        confusion_matrix = cm_norm,
        display_labels   = CLASS_NAMES,
    ).plot(ax=axes[1], cmap="Blues", colorbar=False, values_format=".2%")
    axes[1].set_title("Row-Normalised (Recall per Class)", fontweight="bold")
    axes[1].set_xlabel("Predicted Label")
    axes[1].set_ylabel("True Label")

    plt.tight_layout()

    output_path = "data/08_reporting/confusion_matrix.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    log.info("Confusion matrix saved to %s", output_path)


    # Log the cell-level breakdown
    tn_row = cm[0]   # Normal row
    pr_row = cm[1]   # Prediabetes row
    db_row = cm[2]   # Diabetic row
    log.info("Confusion matrix (raw counts):")
    log.info("  True Normal      → predicted Normal=%d  Prediabetes=%d  Diabetic=%d", *tn_row)
    log.info("  True Prediabetes → predicted Normal=%d  Prediabetes=%d  Diabetic=%d", *pr_row)
    log.info("  True Diabetic    → predicted Normal=%d  Prediabetes=%d  Diabetic=%d", *db_row)
    # log.info("Confusion matrix plot generated (%d bytes).", len(img_bytes))

    return output_path



def plot_roc_curves(
    trained_model: Any,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> str:
    """
    Generate per-class one-vs-rest ROC curves and return as PNG bytes.

    One ROC curve is plotted for each of the three classes using a
    one-vs-rest (OvR) strategy.  The AUC score is annotated in the legend.

    Parameters
    ----------
    trained_model : fitted estimator
    X_test        : test feature matrix
    y_test        : test target (single-column DataFrame)

    Returns
    -------
    bytes — PNG image bytes
    """
    y_1d        = _to_1d(y_test)
    y_pred_prob = trained_model.predict_proba(X_test)

    colors = ["#2ECC71", "#F39C12", "#E74C3C"]  # Normal / Prediabetes / Diabetic

    fig, ax = plt.subplots(figsize=(9, 7))

    for class_idx, (class_name, color) in enumerate(zip(CLASS_NAMES, colors)):
        y_binary = (y_1d == class_idx).astype(int)
        y_scores = y_pred_prob[:, class_idx]

        fpr, tpr, _ = roc_curve(y_binary, y_scores)
        auc_score   = auc(fpr, tpr)

        ax.plot(fpr, tpr, color=color, lw=2.5,
                label=f"{class_name}   AUC = {auc_score:.3f}")

        log.info(
            "ROC — %s : AUC=%.4f",
            class_name, auc_score,
        )

    ax.plot([0, 1], [0, 1], "k--", lw=1.2, label="Random (AUC = 0.500)")
    ax.set_xlabel("False Positive Rate  (1 − Specificity)", fontsize=12)
    ax.set_ylabel("True Positive Rate  (Sensitivity / Recall)", fontsize=12)
    ax.set_title(
        "ROC Curves — One-vs-Rest per Class  (Test Set)",
        fontsize=13, fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = "data/08_reporting/roc_curves.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    log.info("ROC curves saved to %s", output_path)

    return output_path



def compute_shap_values(
    trained_model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[str, str]:
    """
    Compute SHAP values and produce two global explanation plots.

    SHAP (SHapley Additive exPlanations) assigns each feature a contribution
    value grounded in cooperative game theory.  It is the only explainability
    method that simultaneously satisfies:
        - Local accuracy  (SHAP values sum to the model's output)
        - Missingness     (absent features have zero contribution)
        - Consistency     (if a feature matters more in model A than B,
                           its SHAP value is higher in A)

    Plot 1 — SHAP bar chart (mean |SHAP| per feature, per class)
    -------------------------------------------------------------
    Shows which features contribute most on average to predictions for each
    class across the entire test set.  Useful for the project report to
    justify the feature selection and explain the model's behaviour globally.

    Plot 2 — SHAP beeswarm (distribution of SHAP values, Diabetic class)
    --------------------------------------------------------------------
    Each dot = one patient.  X-axis position = SHAP value for the Diabetic
    class (how much that feature's value pushed the prediction toward
    Diabetic).  Dot color = raw feature value (red = high, blue = low).
    This reveals not just which features matter, but HOW they matter.

    Parameters
    ----------
    trained_model : fitted estimator (CatBoost or other tree model)
    X_train       : training features — used as SHAP background dataset
    X_test        : test features — SHAP values are computed for these

    Returns
    -------
    tuple[bytes, bytes]
        (shap_bar_png_bytes, shap_beeswarm_png_bytes)
    """
    log.info("Computing SHAP values with TreeExplainer...")

    try:
        explainer   = shap.TreeExplainer(trained_model)
        shap_values = explainer.shap_values(X_test)
        log.info("TreeExplainer used successfully.")
    except Exception as exc:
        log.warning(
            "TreeExplainer failed (%s) — falling back to KernelExplainer.", exc
        )
        # KernelExplainer is model-agnostic but slower.
        # Sample 100 background rows for speed.
        background  = shap.sample(X_train, 100, random_state=42)
        explainer   = shap.KernelExplainer(trained_model.predict_proba, background)
        shap_values = explainer.shap_values(X_test)

    shap_array = np.array(shap_values)
    log.info("SHAP values computed. Array shape: %s", shap_array.shape)

    # Plot 1: Bar chart — mean |SHAP| per feature per class
    plt.figure(figsize=(11, 7))
    shap.summary_plot(
        shap_values,
        X_test,
        plot_type   = "bar",
        class_names = CLASS_NAMES,
        max_display = 15,
        show        = False,
    )
    plt.title(
        "SHAP Feature Importance — Mean |SHAP| per Class",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()

    bar_output_path = "data/08_reporting/shap_bar.png"

    plt.savefig(
        bar_output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    log.info("SHAP bar chart saved to %s", bar_output_path)

    # Plot 2: Beeswarm — SHAP distributions for the Diabetic class
    if isinstance(shap_values, list):
        sv_diabetic = shap_values[2]   # shape (n_test_samples, n_features)
    else:
        sv_diabetic = shap_values

    plt.figure(figsize=(11, 7))
    shap.summary_plot(
        sv_diabetic,
        X_test,
        plot_type   = "dot",
        max_display = 15,
        show        = False,
    )
    plt.title(
        "SHAP Beeswarm — Diabetic Class  (each dot = one patient)",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()

    beeswarm_output_path = "data/08_reporting/shap_beeswarm.png"

    plt.savefig(
        beeswarm_output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    log.info(
        "SHAP beeswarm plot saved to %s",
        beeswarm_output_path,
    )

    return bar_output_path, beeswarm_output_path



def save_shap_explainer(
    trained_model: Any,
    X_train: pd.DataFrame,
) -> Any:
    """
    Fit and return a SHAP explainer so Kedro can persist it as an artifact.

    Parameters
    ----------
    trained_model : fitted estimator
    X_train       : training features — provides background for the explainer

    Returns
    -------
    shap.TreeExplainer or shap.KernelExplainer
        Fitted explainer object — Kedro persists this to
        data/06_models/shap_explainer.pkl via the catalog.
    """
    log.info("Fitting SHAP explainer for deployment artifact...")

    try:
        explainer = shap.TreeExplainer(trained_model)
        # Sanity check — verify it works on one row before saving
        _ = explainer.shap_values(X_train.iloc[:1])
        log.info("SHAP TreeExplainer fitted and validated.")
    except Exception as exc:
        log.warning(
            "TreeExplainer failed (%s) — using KernelExplainer instead.", exc
        )
        background = shap.sample(X_train, 100, random_state=42)
        explainer  = shap.KernelExplainer(trained_model.predict_proba, background)
        _ = explainer.shap_values(X_train.iloc[:1])
        log.info("SHAP KernelExplainer fitted and validated.")

    return explainer

def compute_lime_explanation(
    trained_model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    model_metadata: dict[str, Any],
) -> str:
    """
    Generate a LIME explanation for one representative test patient and
    return it as a file path.

    WHY LIME alongside SHAP?
    ------------------------
    SHAP and LIME provide complementary perspectives on model behaviour.
    SHAP values are theoretically grounded (Shapley values) and globally
    consistent — all SHAP values sum to the prediction.
    LIME fits a local linear model around one data point, which is simpler
    to communicate to non-technical stakeholders and provides a second
    independent verification of which features matter.

    Including both in the evaluation report strengthens the explainability
    argument in the project documentation and satisfies the architecture
    diagram requirement.

    The patient explained here is the first test patient whose true label
    is Diabetic — chosen because that is the most clinically relevant case.
    """

    feature_names = model_metadata.get("feature_names", X_train.columns.tolist())

    explainer = lime_tabular.LimeTabularExplainer(
        training_data = X_train.values,
        feature_names = feature_names,
        class_names   = ["Normal", "Prediabetes", "Diabetic"],
        mode          = "classification",
        random_state  = 42,
    )

    # Pick first Diabetic patient from the test set for the explanation
    y_pred = trained_model.predict(X_test)
    diabetic_indices = [i for i, p in enumerate(y_pred) if p == 2]
    patient_idx = diabetic_indices[0] if diabetic_indices else 0

    lime_exp = explainer.explain_instance(
        data_row   = X_test.values[patient_idx],
        predict_fn = trained_model.predict_proba,
        num_features = min(10, len(feature_names)),
        num_samples  = 1000,
        labels       = (2,),   # Explain the Diabetic class
    )

    fig = lime_exp.as_pyplot_figure(label=2)
    fig.set_size_inches(12, 7)
    fig.suptitle(
        f"LIME Explanation — Test Patient {patient_idx}  (Predicted: Diabetic)",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()

    output_path = "data/08_reporting/lime_explanation.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    log.info(
        "LIME explanation generated for patient %d and saved to %s",
        patient_idx,
        output_path,
    )

    return output_path



def plot_feature_importance(
    trained_model: Any,
    model_metadata: dict[str, Any],
) -> str:
    """
    Plot the model's native feature importances as a horizontal bar chart.

    WHY native feature importance alongside SHAP?
    ---------------------------------------------
    SHAP global importance (mean |SHAP|) accounts for feature interactions
    and is the most accurate measure of a feature's contribution.
    Native importance (e.g. CatBoost's gain-based importance) is computed
    differently — it measures how often a feature is used in splits and
    by how much it reduces impurity.

    Comparing SHAP importance with native importance:
    - Agreement between methods = strong evidence a feature truly matters
    - Disagreement = worth investigating (possible interaction effects
      or scale sensitivity)

    Including both satisfies the architecture diagram's explainability
    layer requirement and provides a richer evidence base for the report.
    """
    feature_names = model_metadata.get("feature_names", [])

    # Extract importances
    if hasattr(trained_model, "get_feature_importance"):
        # CatBoost
        importances = trained_model.get_feature_importance()
    elif hasattr(trained_model, "feature_importances_"):
        importances = trained_model.feature_importances_
    else:
        log.warning("Model has no native feature importance — skipping plot.")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, "Feature importance not available for this model type.",
                ha="center", va="center", fontsize=12)

        output_path = "data/08_reporting/feature_importance.png"
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        log.info(
            "Feature importance placeholder saved to %s",
            output_path,
        )

        return output_path

    # Sort by importance descending
    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=True)   # ascending for horizontal bar
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = ["#2E75B6" if v >= importance_df["importance"].median()
              else "#AEC6CF"
              for v in importance_df["importance"]]

    ax.barh(importance_df["feature"], importance_df["importance"],
            color=colors, edgecolor="black")
    ax.set_xlabel("Feature Importance (Model-Native)", fontsize=12)
    ax.set_title(
        f"Feature Importance — {model_metadata.get('model_name', 'Model')} (Native)",
        fontsize=13, fontweight="bold",
    )
    ax.axvline(
        x=importance_df["importance"].mean(),
        color="red", linestyle="--", lw=1.5,
        label=f"Mean = {importance_df['importance'].mean():.4f}",
    )
    ax.legend(fontsize=10)

    for bar, val in zip(ax.patches, importance_df["importance"]):
        ax.text(val + 0.001, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9)

    plt.tight_layout()

    output_path = "data/08_reporting/feature_importance.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    log.info(
        "Feature importance plot saved to %s",
        output_path,
    )

    return output_path


def build_evaluation_report(
    test_metrics_output: dict[str, Any],
    model_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Compile all evaluation outputs into one comprehensive JSON report.

    This report is the single source of truth for the model's performance.
    It is saved to data/08_reporting/full_evaluation_report.json and:
        - Used as the basis for the project's evaluation chapter
        - Served by the FastAPI /model/info endpoint
        - Read by the prediction pipeline to include threshold values
          in every prediction response

    Report structure
    ----------------
    model_name            — winning algorithm name
    model_version         — semantic version string ("1.0.0")
    feature_names         — ordered list of features the model uses
    n_features            — integer count of features
    target_encoding       — mapping of integer codes to class name strings
    test_metrics          — dict of six scalar float metrics
    classification_report — per-class precision / recall / F1 / support
    threshold             — Youden-J threshold and risk band definitions
    evaluation_summary    — human-readable one-line summary per metric

    Parameters
    ----------
    test_metrics_output : dict — output of compute_test_metrics
    model_metadata      : dict — loaded from data/08_reporting/model_metadata.json
                                 (saved by the training pipeline)

    Returns
    -------
    dict[str, Any]
        Complete evaluation report — Kedro persists this to
        data/08_reporting/full_evaluation_report.json via the catalog.
    """
    summary_metrics = test_metrics_output["summary_metrics"]
    cls_report      = test_metrics_output["classification_report"]

    # Human-readable one-liner per metric for the /model/info endpoint
    evaluation_summary = {
        "f1_macro"    : (
            f"{summary_metrics['f1_macro']:.4f} — "
            "unweighted mean F1 across Normal / Prediabetes / Diabetic"
        ),
        "f1_weighted" : (
            f"{summary_metrics['f1_weighted']:.4f} — "
            "frequency-weighted mean F1"
        ),
        "accuracy"    : (
            f"{summary_metrics['accuracy']:.4f} — "
            "fraction of all test patients correctly classified"
        ),
        "roc_auc_ovr" : (
            f"{summary_metrics['roc_auc_ovr']:.4f} — "
            "one-vs-rest macro AUC; overall discriminative ability"
        ),
        "recall_macro": (
            f"{summary_metrics['recall_macro']:.4f} — "
            "unweighted mean recall; fraction of each class correctly caught"
        ),
        "precision_macro": (
            f"{summary_metrics['precision_macro']:.4f} — "
            "unweighted mean precision; fraction of positive predictions correct"
        ),
    }

    report = {
        "model_name"           : model_metadata.get("model_name", "Unknown"),
        "model_version"        : model_metadata.get("model_version", "1.0.0"),
        "feature_names"        : model_metadata.get("feature_names", []),
        "n_features"           : model_metadata.get("n_features", 0),
        "target_encoding"      : model_metadata.get("target_encoding", {
            "0": "Normal",
            "1": "Prediabetes",
            "2": "Diabetic",
        }),
        "test_metrics"         : summary_metrics,
        "classification_report": cls_report,
        "threshold"            : model_metadata.get("threshold", {}),
        "evaluation_summary"   : evaluation_summary,
    }

    log.info("=== FULL EVALUATION REPORT ===")
    log.info("  Model         : %s v%s", report["model_name"], report["model_version"])
    log.info("  Features      : %d  → %s", report["n_features"], report["feature_names"])
    log.info("  F1 macro      : %.4f", summary_metrics["f1_macro"])
    log.info("  F1 weighted   : %.4f", summary_metrics["f1_weighted"])
    log.info("  Accuracy      : %.4f", summary_metrics["accuracy"])
    log.info("  ROC AUC OvR   : %.4f", summary_metrics["roc_auc_ovr"])
    log.info("  Recall macro  : %.4f", summary_metrics["recall_macro"])
    log.info("  Precision mac : %.4f", summary_metrics["precision_macro"])

    if report["threshold"]:
        log.info(
            "  Threshold     : opt=%.4f  high=%.4f",
            report["threshold"].get("opt_threshold", 0),
            report["threshold"].get("thresh_high", 0),
        )

    log.info("Full evaluation report compiled successfully.")
    return report


def save_lime_background(
    X_train: pd.DataFrame,
    n_samples: int = 500,
) -> pd.DataFrame:
    """
    Save a representative sample of X_train as the LIME background dataset.

    LIME needs to know the realistic distribution of feature values to
    generate meaningful perturbations around a patient's data point.
    Using a sample of the actual training data is the most accurate approach.

    Saved to data/06_models/lime_background.pkl via the catalog.
    Loaded at startup by ModelLoader alongside the other artifacts.
    """
    background = X_train.sample(
        n=min(n_samples, len(X_train)),
        random_state=42,
    ).reset_index(drop=True)

    log.info(
        "LIME background dataset saved: %d rows x %d features",
        len(background), background.shape[1],
    )
    return background