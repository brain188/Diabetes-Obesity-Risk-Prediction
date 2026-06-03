from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def load_and_inspect(
        data_train: pd.DataFrame,
        data_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    """
    Log basic structural information about the two raw datasets.

    This node performs NO transformations.  Its sole purpose is to give a
    visible audit trail in the Kedro logs so anyone running the pipeline
    can immediately confirm the correct files were loaded and that row /
    column counts match expectations.

    Parameters
    ----------
    data_train : pd.DataFrame
        Raw training dataset loaded from ``diabetes_train_raw``.
    data_test : pd.DataFrame
        Raw test dataset loaded from ``diabetes_test_raw``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        The same two DataFrames, unchanged — passed through to the next node.
    """
    for name, df in [("TRAIN", data_train), ("TEST", data_test)]:
        log.info("--- %s ---", name)
        log.info("  Shape      : %s rows × %s columns", *df.shape)
        log.info("  Columns    : %s", df.columns.tolist())
        log.info(
            "  Target dist: %s",
            df["diabetes_status"].value_counts().to_dict()
            if "diabetes_status" in df.columns
            else "column not found",
        )
        nulls = df.isnull().sum()
        nulls = nulls[nulls > 0]
        if nulls.empty:
            log.info("  Missing    : none")
        else:
            log.info("  Missing    : %s", nulls.to_dict())

        duplicate_count = df.duplicated().sum()

        if duplicate_count == 0:
            log.info("  Duplicates : none")
        else:
            log.info(
                "  Duplicates : %s rows (%.2f%%)",
                duplicate_count,
                (duplicate_count / len(df)) * 100,
            )

    return data_train, data_test


def select_columns(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    columns_to_keep: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Keep only the agreed feature columns and the target; drop everything else.

    Parameters
    ----------
    data_train : pd.DataFrame
        Raw training DataFrame (output of ``load_and_inspect``).
    data_test : pd.DataFrame
        Raw test DataFrame (output of ``load_and_inspect``).
    columns_to_keep : list[str]
        Column names to retain, read from
        ``conf/base/parameters.yml``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (train, test) DataFrames with only the selected columns.
    """
    def _select(df: pd.DataFrame, split: str) -> pd.DataFrame:
        missing = [c for c in columns_to_keep if c not in df.columns]
        if missing:
            raise ValueError(
                f"[{split}] Expected columns not found: {missing}. "
                "Update keep_columns in parameters.yml."
            )
        result = df[columns_to_keep].copy()
        dropped = df.shape[1] - result.shape[1]
        log.info("[%s] Columns kept: %d  |  dropped: %d", split, result.shape[1], dropped)
        return result

    train = _select(data_train, "TRAIN")
    test  = _select(data_test,  "TEST")
    return train, test


def encode_target(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    target_map: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Encode the ``diabetes_status`` target column from strings to integers.

    Encoding
    --------
    ``Normal``      =  0
    ``Prediabetes`` =  1
    ``Diabetic``    =  2

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame
    target_map : dict
        Mapping of string label → integer, e.g.
        ``{"normal": 0, "prediabetes": 1, "diabetic": 2}``.
        Read from ``conf/base/parameters.yml``.
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        DataFrames with ``diabetes_status`` replaced by its integer encoding.
    """
    def _encode(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        # Keep raw string for reference / reporting
        df["diabetes_status_raw"] = df["diabetes_status"].astype(str).str.strip()

        # Apply mapping (case-insensitive)
        encoded = (
            df["diabetes_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(target_map)
        )

        unmapped = encoded.isna().sum()
        if unmapped > 0:
            bad_vals = df.loc[encoded.isna(), "diabetes_status"].unique().tolist()
            raise ValueError(
                f"[{split}] {unmapped} rows have unrecognised target values: "
                f"{bad_vals}.  Update target_map in data_processing.yml."
            )

        df["diabetes_status"] = encoded.astype(int)

        log.info("[%s] Target encoded:", split)
        for label, code in sorted(target_map.items(), key=lambda x: x[1]):
            count = (df["diabetes_status"] == code).sum()
            pct   = count / len(df) * 100
            log.info("  %d = %-14s : %6d  (%.1f%%)", code, label, count, pct)

        return df

    train = _encode(data_train, "TRAIN")
    test  = _encode(data_test,  "TEST")
    return train, test


def encode_booleans(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    bool_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert boolean columns from mixed True/False representations to integers.

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame
    bool_columns : list[str]
        Column names to treat as booleans, from ``parameters.yml``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
    """
    TRUTHY = {"true", "1", "yes"}

    def _encode_bool_col(series: pd.Series) -> pd.Series:
        return (
            series.astype(str)
            .str.strip()
            .str.lower()
            .map(lambda v: 1 if v in TRUTHY else 0)
            .astype(int)
        )

    def _encode(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        for col in bool_columns:
            if col not in df.columns:
                log.warning("[%s] Boolean column '%s' not found — skipped.", split, col)
                continue
            df[col] = _encode_bool_col(df[col])
        log.info("[%s] Boolean columns encoded: %s", split, bool_columns)
        return df

    train = _encode(data_train, "TRAIN")
    test  = _encode(data_test,  "TEST")
    return train, test



def encode_bmi_category(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    bmi_map: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Encode ``bmi_category`` as an ordinal integer.

    Ordinal mapping
    ``Normal``     → 0
    ``Overweight`` → 1
    ``Obese I``    → 2
    ``Obese II+``  → 3

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame
    bmi_map : dict
        Mapping of lowercase BMI category string → integer, from
        ``parameters.yml``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
    """
    def _encode(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        encoded = (
            df["bmi_category"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(bmi_map)
        )
        unknown = encoded.isna().sum()
        if unknown > 0:
            bad = df.loc[encoded.isna(), "bmi_category"].unique().tolist()
            log.warning(
                "[%s] %d unknown bmi_category values → assigned -1: %s",
                split, unknown, bad,
            )
            encoded = encoded.fillna(-1)

        df["bmi_category"] = encoded.astype(int)
        log.info(
            "[%s] bmi_category encoded. Unique values: %s",
            split, sorted(df["bmi_category"].unique().tolist()),
        )
        return df

    train = _encode(data_train, "TRAIN")
    test  = _encode(data_test,  "TEST")
    return train, test



def encode_sex(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    sex_map: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Encode the ``sex`` column as a binary integer.

    Mapping
    -------
    ``Female`` → 0
    ``Male``   → 1

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame
    sex_map : dict
        Mapping from ``parameters`{"female": 0, "male": 1}``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
    """
    def _encode(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        encoded = (
            df["sex"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(sex_map)
        )
        unknown = encoded.isna().sum()
        if unknown > 0:
            bad = df.loc[encoded.isna(), "sex"].unique().tolist()
            raise ValueError(
                f"[{split}] Unrecognised sex values: {bad}. "
                "Update sex_map in parameters.yml"
            )
        df["sex"] = encoded.astype(int)
        log.info("[%s] sex encoded — unique values: %s", split, sorted(df["sex"].unique().tolist()))
        return df

    train = _encode(data_train, "TRAIN")
    test  = _encode(data_test,  "TEST")
    return train, test



def encode_residence(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
    residence_map: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Encode the ``residence`` column as a binary integer.

    Mapping
    -------
    ``Rural`` → 0
    ``Urban`` → 1

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame
    residence_map : dict
        From ``parameters.yml``,``{"rural": 0, "urban": 1}``.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
    """
    def _encode(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        encoded = (
            df["residence"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(residence_map)
        )
        unknown = encoded.isna().sum()
        if unknown > 0:
            bad = df.loc[encoded.isna(), "residence"].unique().tolist()
            raise ValueError(
                f"[{split}] Unrecognised residence values: {bad}. "
                "Update residence_map in parameters.yml."
            )
        df["residence"] = encoded.astype(int)
        log.info("[%s] residence encoded — unique values: %s", split, sorted(df["residence"].unique().tolist()))
        return df

    train = _encode(data_train, "TRAIN")
    test  = _encode(data_test,  "TEST")
    return train, test



def convert_age(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert the ``age`` column from float to integer (floor truncation).

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
    """
    def _convert(df: pd.DataFrame, split: str) -> pd.DataFrame:
        df = df.copy()
        df["age"] = df["age"].astype(float).astype(int)
        log.info(
            "[%s] age converted to int. Range: %d – %d",
            split, df["age"].min(), df["age"].max(),
        )
        return df

    train = _convert(data_train, "TRAIN")
    test  = _convert(data_test,  "TEST")
    return train, test


 
def final_quality_check(
    data_train: pd.DataFrame,
    data_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run a final quality gate before the data leaves the processing pipeline.

    Parameters
    ----------
    data_train : pd.DataFrame
    data_test : pd.DataFrame

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        The same DataFrames if all checks pass.

    Raises
    ------
    ValueError
        If any data quality check fails.
    """
    EXPECTED_TARGET_VALUES = {0, 1, 2}

    def _check(df: pd.DataFrame, split: str) -> pd.DataFrame:
        # Check 1 — no missing values
        null_counts = df.isnull().sum()
        nulls = null_counts[null_counts > 0]
        if not nulls.empty:
            raise ValueError(
                f"[{split}] Missing values found after processing: {nulls.to_dict()}"
            )
 
        # Check 2 — all columns numeric
        non_numeric = df.select_dtypes(exclude=[np.number]).columns.tolist()
        # Allow the raw label column to remain as object
        non_numeric = [c for c in non_numeric if c != "diabetes_status_raw"]
        if non_numeric:
            raise ValueError(
                f"[{split}] Non-numeric columns remain after encoding: {non_numeric}. "
                "All columns must be numeric before training."
            )
 
        # Check 3 — target values are valid
        actual_vals = set(df["diabetes_status"].unique())
        invalid = actual_vals - EXPECTED_TARGET_VALUES
        if invalid:
            raise ValueError(
                f"[{split}] Unexpected target values: {invalid}. "
                f"Expected only {EXPECTED_TARGET_VALUES}."
            )

        log.info("[%s]  All quality checks passed.", split)
        log.info("[%s]   Final shape : %d rows × %d cols", split, *df.shape)
        log.info("[%s]   Dtypes      : %s", split, df.dtypes.to_dict())
        log.info(
            "[%s]   Target dist : %s",
            split,
            df["diabetes_status"].value_counts().sort_index().to_dict(),
        )
        return df

    train = _check(data_train, "TRAIN")
    test  = _check(data_test,  "TEST")
    return train, test