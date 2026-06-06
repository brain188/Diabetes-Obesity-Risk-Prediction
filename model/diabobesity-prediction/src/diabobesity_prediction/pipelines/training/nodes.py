from __future__ import annotations

import logging
from typing import Any

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from xgboost import XGBClassifier

log = logging.getLogger(__name__)


def _to_1d(y: pd.DataFrame | pd.Series | np.ndarray) -> np.ndarray:
    """
    Convert any target representation to a flat 1-D numpy array.

    The feature_engineering pipeline saves y as a single-column DataFrame
    so Parquet serialisation works.  Sklearn, XGBoost, LightGBM, and
    CatBoost all require a 1-D array.  This helper handles every possible
    input type so every node stays clean.

    Parameters
    ----------
    y : pd.DataFrame, pd.Series, or np.ndarray
        Target in any supported shape.

    Returns
    -------
    np.ndarray  — shape (n,), dtype int
    """
    if isinstance(y, pd.DataFrame):
        return y.iloc[:, 0].to_numpy(dtype=int)
    if isinstance(y, pd.Series):
        return y.to_numpy(dtype=int)
    return np.asarray(y, dtype=int).ravel()

def _compute_metrics(
    model: Any,
    X: pd.DataFrame,
    y: pd.DataFrame | pd.Series | np.ndarray,
    split_name: str,
) -> dict[str, float]:
    """
    Compute the full metric suite for a fitted model on one data split.

    Metrics
    -------
    accuracy       — overall fraction of correct predictions
    f1_macro       — unweighted mean F1 across all three classes; the primary
                     selection metric because it treats every class equally,
                     which matters for the imbalanced Prediabetes / Normal classes
    f1_weighted    — class-frequency-weighted F1; useful secondary view
    precision_macro— unweighted mean precision across all classes
    recall_macro   — unweighted mean recall; high recall = fewer missed patients
    roc_auc_ovr    — one-vs-rest multi-class AUC; measures overall discrimination

    Parameters
    ----------
    model      : fitted sklearn-compatible estimator
    X          : feature matrix
    y          : true labels
    split_name : label for log messages ("VAL" or "TEST")

    Returns
    -------
    dict[str, float]  — all metric values rounded to 4 decimal places
    """
    y_1d        = _to_1d(y)
    y_pred      = model.predict(X)
    y_pred_prob = model.predict_proba(X)

    metrics = {
        "accuracy"       : round(float(accuracy_score(y_1d, y_pred)),                              4),
        "f1_macro"       : round(float(f1_score(y_1d, y_pred,       average="macro",  zero_division=0)), 4),
        "f1_weighted"    : round(float(f1_score(y_1d, y_pred,       average="weighted", zero_division=0)), 4),
        "precision_macro": round(float(precision_score(y_1d, y_pred, average="macro",  zero_division=0)), 4),
        "recall_macro"   : round(float(recall_score(y_1d, y_pred,    average="macro",  zero_division=0)), 4),
        "roc_auc_ovr"    : round(float(roc_auc_score(y_1d, y_pred_prob, multi_class="ovr", average="macro")), 4),
    }

    log.info("[%s] Metrics:", split_name)
    for name, value in metrics.items():
        log.info("  %-20s : %.4f", name, value)

    return metrics



def train_candidates(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
    mlflow_experiment_name: str,
    cv_folds: int,
    random_state: int,
) -> dict[str, dict]:
    """
    Train five candidate algorithms and evaluate each on the validation set.

    Algorithms
    ----------
    1.  Logistic Regression  — linear baseline; fast; interpretable coefficients
    2.  Random Forest        — bagging ensemble; robust to noise; built-in
                               feature importance
    3.  XGBoost              — gradient boosting; typically strongest on
                               tabular data
    4.  LightGBM             — fast gradient boosting; memory-efficient
    5.  CatBoost             — gradient boosting with ordered boosting;
                               often strong out-of-the-box

    Parameters
    ----------
    X_train, y_train  : SMOTE-balanced training arrays
    X_val, y_val      : unmodified validation arrays (real distribution)
    mlflow_experiment_name : MLflow experiment to log runs under
    cv_folds          : number of cross-validation folds (default 5)
    random_state      : seed for reproducibility

    Returns
    -------
    dict[str, dict]
        Keys are model names; values are dicts containing:
        ``model``       — fitted estimator
        ``val_metrics`` — metric dict from the validation set
        ``cv_f1_mean``  — mean CV F1-macro score
        ``cv_f1_std``   — std  CV F1-macro score
    """

    y_train_1d = _to_1d(y_train)
    y_val_1d   = _to_1d(y_val)

    # mlflow.set_experiment(mlflow_experiment_name)

    candidates = {
        "LogisticRegression": LogisticRegression(
            max_iter     = 1000,
            random_state = random_state,
            C            = 1.0,
            class_weight = "balanced",
            solver       = "lbfgs",
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators = 200,
            max_depth    = 10,
            min_samples_leaf = 5,
            class_weight = "balanced",
            random_state = random_state,
            n_jobs       = -1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators     = 200,
            max_depth        = 6,
            learning_rate    = 0.05,
            subsample        = 0.8,
            colsample_bytree = 0.8,
            eval_metric      = "mlogloss",
            objective        = "multi:softprob",
            num_class        = 3,
            random_state     = random_state,
            verbosity        = 0,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators  = 200,
            max_depth     = 6,
            learning_rate = 0.05,
            num_leaves    = 63,
            class_weight  = "balanced",
            objective     = "multiclass",
            num_class     =  3,
            random_state  = random_state,
            verbose       = -1,
        ),
        "CatBoost": CatBoostClassifier(
            iterations   = 200,
            depth        = 6,
            learning_rate = 0.05,
            loss_function = "MultiClass",
            random_seed  = random_state,
            verbose      = 0,
        ),
    }

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    results: dict[str, dict] = {}

    for model_name, model in candidates.items():
        log.info("Training candidate: %s", model_name)

        with mlflow.start_run(run_name=f"candidate_{model_name}", nested = True):

            # Cross-validation on training set
            cv_scores = cross_val_score(
                model, X_train, y_train_1d,
                cv      = cv,
                scoring = "f1_macro",
                n_jobs  = -1,
            )
            cv_mean = round(float(cv_scores.mean()), 4)
            cv_std  = round(float(cv_scores.std()),  4)

            log.info(
                "  CV F1-macro : %.4f ± %.4f  (folds: %s)",
                cv_mean, cv_std,
                [round(s, 4) for s in cv_scores],
            )

            # Full fit on training set
            model.fit(X_train, y_train_1d)

            # Evaluate on validation set
            val_metrics = _compute_metrics(model, X_val, y_val_1d, "VAL")

            # Log everything to MLflow
            mlflow.log_param("model_name",   model_name)
            mlflow.log_param("cv_folds",     cv_folds)
            mlflow.log_metric("cv_f1_mean",  cv_mean)
            mlflow.log_metric("cv_f1_std",   cv_std)
            for metric_name, value in val_metrics.items():
                mlflow.log_metric(f"val_{metric_name}", value)

            mlflow.sklearn.log_model(model, name=model_name)

        results[model_name] = {
            "model"      : model,
            "val_metrics": val_metrics,
            "cv_f1_mean" : cv_mean,
            "cv_f1_std"  : cv_std,
        }
        log.info(
            "  %s done — val F1-macro=%.4f  CV F1-macro=%.4f±%.4f",
            model_name,
            val_metrics["f1_macro"],
            cv_mean, cv_std,
        )

    return results



def select_best_model(
    candidate_results: dict[str, dict],
) -> tuple[Any, str, dict]:
    """
    Select the best-performing candidate model based on validation F1-macro.

    Parameters
    ----------
    candidate_results : dict[str, dict]
        Output of ``train_candidates`` — keyed by model name.

    Returns
    -------
    tuple[Any, str, dict]
        (best_model, best_model_name, best_val_metrics)
    """
    # Build a comparison DataFrame
    rows = []
    for name, result in candidate_results.items():
        row = {"model_name": name, "cv_f1_mean": result["cv_f1_mean"]}
        row.update(result["val_metrics"])
        rows.append(row)

    comparison = (
        pd.DataFrame(rows)
        .sort_values(["f1_macro", "roc_auc_ovr"], ascending=False)
        .reset_index(drop=True)
    )

    log.info("Candidate model ranking (sorted by val F1-macro):")
    log.info("\n%s", comparison.to_string(index=False))

    best_name    = comparison.iloc[0]["model_name"]
    best_result  = candidate_results[best_name]
    best_model   = best_result["model"]
    best_metrics = best_result["val_metrics"]

    log.info(
        "Best model selected: %s  (val F1-macro=%.4f)",
        best_name, best_metrics["f1_macro"],
    )

    return best_model, best_name, best_metrics



def evaluate_final_model(
    best_model: Any,
    best_model_name: str,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
    mlflow_experiment_name: str,
) -> dict[str, Any]:
    """
    Tune the classification threshold on the validation set using Youden J,
    then evaluate the final model on the held-out test set.

    Threshold tuning — Youden J on the Diabetic class (class 2)
    ------------------------------------------------------------
    We treat class 2 (Diabetic) as the positive class and everything else
    (Normal + Prediabetes) as negative.  We find the threshold on
    P(class=2) that maximises Youden's J statistic:

        J = Sensitivity + Specificity - 1

    This gives the operating point that best balances catching real Diabetic
    patients (sensitivity) against avoiding false alarms (specificity).

    From this optimal threshold we define three clinical risk bands:
        Low risk     : P(Diabetic) < OPT_THRESH
        Moderate risk: OPT_THRESH <= P(Diabetic) < OPT_THRESH + 0.20
        High risk    : P(Diabetic) >= OPT_THRESH + 0.20

    The threshold and risk bands are stored in the evaluation report so the
    FastAPI prediction endpoint uses the same values.

      Parameters
    ----------
    best_model       : fitted estimator from select_best_model
    best_model_name  : string name for logging
    X_val, y_val     : validation set — used for threshold tuning ONLY
    X_test, y_test   : held-out test set — used for final evaluation ONLY
    mlflow_experiment_name : MLflow experiment name

    Returns
    -------
    dict[str, Any]
        Full evaluation report: test metrics, thresholds, per-class report.

    """

    y_val_1d  = _to_1d(y_val)

    # Threshold tuning on validation set
    # Predict probabilities on validation set
    y_val_prob = best_model.predict_proba(X_val)

    # Binary OvR on Diabetic class (class 2)
    y_val_binary = (y_val_1d == 2).astype(int)     # 1 = Diabetic, 0 = everything else
    y_val_prob2  = y_val_prob[:, 2]                # probability of class 2

    fpr, tpr, thresholds = roc_curve(y_val_binary, y_val_prob2)
    youden_j   = tpr - fpr
    best_idx   = int(np.argmax(youden_j))
    opt_thresh = float(thresholds[best_idx])

    thresh_low_high = opt_thresh
    thresh_high     = min(opt_thresh + 0.20, 0.90)

    log.info("[evaluate_final_model] Threshold tuning (Youden J on validation):")
    log.info("  Optimal threshold : %.4f  (Youden J = %.4f)", opt_thresh, youden_j[best_idx])
    log.info("  Sensitivity       : %.4f", tpr[best_idx])
    log.info("  Specificity       : %.4f", 1 - fpr[best_idx])
    log.info("  Risk bands (P(Diabetic)):")
    log.info("    Low      : P < %.4f", thresh_low_high)
    log.info("    Moderate : %.4f <= P < %.4f", thresh_low_high, thresh_high)
    log.info("    High     : P >= %.4f", thresh_high)

    log.info("Evaluating final model on TEST SET.")

    y_test_1d = _to_1d(y_test)

    # Compute metrics
    test_metrics = _compute_metrics(best_model, X_test, y_test_1d, "TEST")

    # Per-class report
    y_pred = best_model.predict(X_test)
    report = classification_report(
        y_test_1d, y_pred,
        target_names=["Normal", "Prediabetes", "Diabetic"],
        output_dict=True,
    )

    log.info("Classification report (test set):\n%s",
             classification_report(
                 y_test_1d, y_pred,
                 target_names=["Normal", "Prediabetes", "Diabetic"],
             ))

    # Log to MLflow
    # mlflow.set_experiment(mlflow_experiment_name)
    with mlflow.start_run(run_name=f"final_{best_model_name}", nested = True):
        mlflow.log_param("model_name",      best_model_name)
        mlflow.log_param("evaluation_set",  "test")
        mlflow.log_metric("opt_threshold",    opt_thresh)
        mlflow.log_metric("youden_j",         float(youden_j[best_idx]))
        mlflow.log_metric("sensitivity",      float(tpr[best_idx]))
        mlflow.log_metric("specificity",      float(1 - fpr[best_idx]))
        for metric_name, value in test_metrics.items():
            mlflow.log_metric(f"test_{metric_name}", value)
        mlflow.sklearn.log_model(best_model, name="final_model")

    # Assemble and return the full evaluation report
    evaluation_report = {
        "model_name"           : best_model_name,
        "test_metrics"         : test_metrics,
        "classification_report": report,
        "threshold": {
            "opt_threshold"    : round(opt_thresh, 6),
            "thresh_low_high"  : round(thresh_low_high, 6),
            "thresh_high"      : round(thresh_high, 6),
            "youden_j"         : round(float(youden_j[best_idx]), 6),
            "sensitivity"      : round(float(tpr[best_idx]), 6),
            "specificity"      : round(float(1 - fpr[best_idx]), 6),
            "description": {
                "low"     : f"P(Diabetic) < {thresh_low_high:.4f}",
                "moderate": f"{thresh_low_high:.4f} <= P(Diabetic) < {thresh_high:.4f}",
                "high"    : f"P(Diabetic) >= {thresh_high:.4f}",
            },
        },
    }

    return evaluation_report



def save_model_artifacts(
    best_model: Any,
    best_model_name: str,
    evaluation_report: dict[str, Any],
    scaler: Any,
) -> tuple[Any, dict[str, Any]]:
    """
    Assemble the model metadata record that Kedro will persist via the catalog.

    Parameters
    ----------
    tuned_model       : final fitted estimator
    best_model_name   : string identifier
    evaluation_report : output of ``evaluate_final_model``
    scaler            : fitted MinMaxScaler from feature_engineering pipeline

    Returns
    -------
    tuple[Any, dict[str, Any]]
        Model metadata dict (also persisted to disk via catalog).
    """
    feature_names = list(scaler.feature_names_in_) if hasattr(scaler, "feature_names_in_") else []

    metadata = {
        "model_name"    : best_model_name,
        "model_version" : "1.0.0",
        "feature_names" : feature_names,
        "n_features"    : len(feature_names),
        "target_encoding": {
            "0": "Normal",
            "1": "Prediabetes",
            "2": "Diabetic",
        },
        "test_metrics"  : evaluation_report["test_metrics"],
        "threshold"    : evaluation_report["threshold"],
        "classification_report": evaluation_report["classification_report"],
    }

    log.info("Model artifacts assembled.")
    log.info("  Model name    : %s", best_model_name)
    log.info("  Feature names : %s", feature_names)
    log.info("  Test metrics  :")
    for k, v in evaluation_report["test_metrics"].items():
        log.info("    %-20s : %.4f", k, v)
    log.info("  Thresholds:")
    log.info("    opt_threshold  : %.4f", evaluation_report["threshold"]["opt_threshold"])
    log.info("    thresh_high    : %.4f", evaluation_report["threshold"]["thresh_high"])

    return best_model, metadata