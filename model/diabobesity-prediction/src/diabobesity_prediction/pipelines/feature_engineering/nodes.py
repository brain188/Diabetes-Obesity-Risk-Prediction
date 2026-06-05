from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

log = logging.getLogger(__name__)


def split_train_validation(
    data_train_cleaned: pd.DataFrame,
    val_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the cleaned training DataFrame into train and validation subsets.
 
    Parameters
    ----------
    data_train_cleaned : pd.DataFrame
        Cleaned training DataFrame from the data_processing pipeline.
        Must contain the ``diabetes_status`` column.
    val_size : float
        Fraction of training rows to reserve for validation.
        Read from ``conf/base/parameters.yml``.
    random_state : int
        Seed for reproducibility.
 
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (train_split, val_split) — both retain ALL columns including the target.
    """
    train_split, val_split = train_test_split(
        data_train_cleaned,
        test_size    = val_size,
        stratify     = data_train_cleaned["diabetes_status"],
        random_state = random_state,
        shuffle      = True,
    )
 
    train_split = train_split.reset_index(drop=True)
    val_split   = val_split.reset_index(drop=True)
 
    log.info(
        "Train / val split complete  "
        "(val_size=%.2f, random_state=%d, stratified=True)",
        val_size, random_state,
    )
    log.info(
        "  Train split : %d rows  |  Val split : %d rows",
        len(train_split), len(val_split),
    )
 
    for name, df in [("Train", train_split), ("Val", val_split)]:
        dist = df["diabetes_status"].value_counts().sort_index().to_dict()
        pcts = {k: f"{v/len(df)*100:.1f}%" for k, v in dist.items()}
        log.info("  %s class dist → %s", name, pcts)
 
    return train_split, val_split


def separate_features_target(
    train_split: pd.DataFrame,
    val_split: pd.DataFrame,
    data_test_cleaned: pd.DataFrame,
    target_col: str,
    drop_cols: list[str],
) -> tuple[
    pd.DataFrame, pd.Series,
    pd.DataFrame, pd.Series,
    pd.DataFrame, pd.Series,
]:
    """
    Separate the feature matrix (X) from the target vector (y) for all three
    splits.
 
    Parameters
    ----------
    train_split : pd.DataFrame
        80 % training subset from ``split_train_validation``.
    val_split : pd.DataFrame
        20 % validation subset from ``split_train_validation``.
    data_test_cleaned : pd.DataFrame
        Cleaned test DataFrame from the data_processing pipeline.
    target_col : str
        Name of the encoded integer target column (``diabetes_status``).
    drop_cols : list[str]
        All column names to exclude from X (target + raw label).
        Read from ``conf/base/parameters.yml``.
 
    Returns
    -------
    6-tuple : X_train, y_train, X_val, y_val, X_test, y_test
    """
    def _split(df: pd.DataFrame, split_name: str):
        cols_to_drop = [c for c in drop_cols if c in df.columns]
        X = df.drop(columns=cols_to_drop).copy()
        # return Dataframe with single column instead of series
        y = df[[target_col]].astype(int).copy()
        y.columns = [target_col]  # ensure target column is named consistently
        log.info(
            "[%s] X shape: %s  |  y shape: %s  |  features: %s",
            split_name, X.shape, y.shape, X.columns.tolist(),
        )
        return X, y
 
    X_train, y_train = _split(train_split,        "TRAIN")
    X_val,   y_val   = _split(val_split,           "VAL")
    X_test,  y_test  = _split(data_test_cleaned,   "TEST")
 
    return X_train, y_train, X_val, y_val, X_test, y_test
 

 
def scale_features(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, MinMaxScaler]:
    """
    Scale all features to the [0, 1] range using MinMaxScaler.
 
    Parameters
    ----------
    X_train : pd.DataFrame
        Training feature matrix (pre-scaling).
    X_val : pd.DataFrame
        Validation feature matrix.
    X_test : pd.DataFrame
        Test feature matrix.
 
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, MinMaxScaler]
        (X_train_scaled, X_val_scaled, X_test_scaled, fitted_scaler)
        The fitted scaler is returned so it can be saved as an artifact and
        reused at inference time.
    """
    scaler = MinMaxScaler()
 
    # Fit only on training data
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns = X_train.columns,
    )
 
    # Apply the same fitted scaler to validation and test
    X_val_scaled = pd.DataFrame(
        scaler.transform(X_val),
        columns = X_val.columns,
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns = X_test.columns,
    )
 
    log.info("MinMaxScaler fitted on training set only.")
    log.info(
        "  X_train_scaled : %s  min=%.4f  max=%.4f",
        X_train_scaled.shape,
        float(X_train_scaled.min().min()),
        float(X_train_scaled.max().max()),
    )
    log.info("  X_val_scaled   : %s", X_val_scaled.shape)
    log.info("  X_test_scaled  : %s", X_test_scaled.shape)
 
    # Log per-feature min/max from the scaler for audit purposes
    for col, lo, hi in zip(
        X_train.columns,
        scaler.data_min_,
        scaler.data_max_,
    ):
        log.info("  %-35s  raw range [%.2f, %.2f]", col, lo, hi)
 
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler
 

 
def apply_smote(
    X_train_scaled: pd.DataFrame,
    y_train: pd.DataFrame,
    smote_random_state: int,
    smote_k_neighbors: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply SMOTE to the training set to address severe class imbalance.
 
    Parameters
    ----------
    X_train_scaled : pd.DataFrame
        Scaled training feature matrix.
    y_train : pd.DataFrame
        Training target matrix (integer-encoded).
    smote_random_state : int
        Seed for reproducibility.
    smote_k_neighbors : int
        Number of nearest neighbours used to generate synthetic samples.
 
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (X_train_resampled, y_train_resampled) — balanced training set.
    """

    # Extract 1D array for SMOTE
    y_train_arr = y_train.iloc[:, 0].values

    # Log class distribution before SMOTE
    before = pd.Series(y_train_arr).value_counts().sort_index()
    log.info("Class distribution before SMOTE:")
    for cls, cnt in before.items():
        log.info("  Class %d : %6d samples  (%.1f%%)", cls, cnt, cnt / len(y_train) * 100)
 
    smote = SMOTE(
        random_state = smote_random_state,
        k_neighbors  = smote_k_neighbors,
    )
 
    X_resampled_arr, y_resampled_arr = smote.fit_resample(X_train_scaled, y_train_arr)
 
    # Wrap back into DataFrame / Series with original column names
    X_train_resampled = pd.DataFrame(
        X_resampled_arr,
        columns = X_train_scaled.columns,
    )
    y_train_resampled = pd.DataFrame(
        y_resampled_arr,
        columns = y_train.columns,
    )
 
    # Log class distribution after SMOTE
    after = y_train_resampled.iloc[:, 0].value_counts().sort_index()
    log.info("Class distribution after SMOTE:")
    for cls, cnt in after.items():
        log.info("  Class %d : %6d samples  (%.1f%%)", cls, cnt, cnt / len(y_train_resampled) * 100)
 
    log.info(
        "SMOTE complete. Training set grew from %d → %d rows.",
        len(y_train), len(y_train_resampled),
    )
 
    return X_train_resampled, y_train_resampled
 

 
def final_feature_check(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> tuple[
    pd.DataFrame, pd.DataFrame,
    pd.DataFrame, pd.DataFrame,
    pd.DataFrame, pd.DataFrame,
]:
    """
    Run a final integrity check on all six outputs before they leave this
    pipeline and enter the training pipeline.
 
    Parameters
    ----------
    X_train, y_train : training features and labels (post-SMOTE)
    X_val,   y_val   : validation features and labels (no SMOTE)
    X_test,  y_test  : test features and labels (no SMOTE)
 
    Returns
    -------
    All six inputs unchanged if every check passes.
    """
    VALID_CLASSES = {0, 1, 2}
 
    splits = [
        ("TRAIN", X_train, y_train),
        ("VAL",   X_val,   y_val),
        ("TEST",  X_test,  y_test),
    ]
 
    for name, X, y in splits:
        
        y_vals = y.iloc[:, 0]

        # Check no missing values in X
        null_X = X.isnull().sum().sum()
        if null_X > 0:
            raise ValueError(
                f"[{name}] Feature matrix has {null_X} missing values "
                "after feature engineering."
            )
 
        # Check no missing values in y
        null_y = y.isnull().sum().sum()
        if null_y > 0:
            raise ValueError(
                f"[{name}] Target vector has {null_y} missing values."
            )
 
        # Check feature values in [0, 1]
        if name == "TRAIN":
            x_min = float(X.min().min())
            x_max = float(X.max().max())

            if x_min < -1e-6 or x_max > 1.0 + 1e-6:
                raise ValueError(
                    f"[{name}] Feature values out of [0, 1] range: "
                    f"min={x_min:.6f}, max={x_max:.6f}. "
                    "Check MinMaxScaler was applied correctly."
                )
 
        # Check target values are valid
        invalid_classes = set(y_vals.unique()) - VALID_CLASSES
        if invalid_classes:
            raise ValueError(   
                f"[{name}] Unexpected target values: {invalid_classes}. "
                f"Expected only {VALID_CLASSES}."
            )
 
        log.info("[%s]   All feature checks passed.", name)
        log.info("[%s]   X shape : %s", name, X.shape)
        log.info("[%s]   y shape : %s", name, y.shape)
        dist = y_vals.value_counts().sort_index()
        for cls, cnt in dist.items():
            log.info(
                "[%s]   Class %d : %6d samples (%.1f%%)",
                name, cls, cnt, cnt / len(y) * 100,
            )
 
    # Check same feature columns across all splits
    if not (X_train.columns.tolist() == X_val.columns.tolist() == X_test.columns.tolist()):
        raise ValueError(
            "Feature column mismatch across splits. "
            f"Train: {X_train.columns.tolist()} | "
            f"Val: {X_val.columns.tolist()} | "
            f"Test: {X_test.columns.tolist()}"
        )
 
    log.info("Feature column consistency verified across all splits.")
 
    return X_train, y_train, X_val, y_val, X_test, y_test
 
 