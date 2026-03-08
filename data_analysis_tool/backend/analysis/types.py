"""Detect per-column types and dataset-level characterization."""
from typing import Any, Dict, List

import pandas as pd

TARGET_HINTS = ("target", "label", "outcome", "y", "class", "error", "result")
DATETIME_HINTS = ("date", "time", "datetime", "timestamp", "created", "updated")


def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """Infer type for each column: numeric_continuous, numeric_discrete, categorical, datetime, text, boolean."""
    out: Dict[str, str] = {}
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            out[col] = "unknown"
            continue
        dtype = df[col].dtype
        col_lower = col.lower()

        if pd.api.types.is_bool_dtype(dtype) or s.nunique() == 2 and set(s.astype(str).unique()).issubset({"True", "False", "1", "0", "yes", "no"}):
            out[col] = "boolean"
            continue

        if pd.api.types.is_numeric_dtype(dtype):
            n = s.nunique()
            # discrete if few unique values relative to length
            if n <= 20 or n / max(len(s), 1) < 0.1:
                out[col] = "numeric_discrete"
            else:
                out[col] = "numeric_continuous"
            continue

        if pd.api.types.is_datetime64_any_dtype(dtype):
            out[col] = "datetime"
            continue

        # Try parsing as datetime
        try:
            parsed = pd.to_datetime(s, errors="coerce")
            if parsed.notna().sum() / max(len(s), 1) > 0.8:
                out[col] = "datetime"
                continue
        except Exception:
            pass

        # String columns
        sample = s.astype(str)
        avg_len = sample.str.len().mean()
        unique_ratio = sample.nunique() / max(len(s), 1)
        if any(h in col_lower for h in DATETIME_HINTS) and avg_len in range(8, 30):
            try:
                pd.to_datetime(sample, errors="coerce")
                out[col] = "datetime"
                continue
            except Exception:
                pass
        if unique_ratio < 0.5 and sample.nunique() <= 50:
            out[col] = "categorical"
        elif avg_len > 100 or sample.nunique() == len(s):
            out[col] = "text"
        else:
            out[col] = "categorical"
    return out


def characterize_dataset(df: pd.DataFrame, column_types: Dict[str, str]) -> Dict[str, Any]:
    """
    Dataset-level: time_series, classification, regression, or generic.
    Optionally detect target column.
    """
    characterization: Dict[str, Any] = {
        "kind": "generic",
        "target_column": None,
        "datetime_column": None,
        "numeric_columns": [],
        "categorical_columns": [],
    }
    for col in df.columns:
        t = column_types.get(col, "")
        if t == "datetime":
            characterization["datetime_column"] = col
        if t in ("numeric_continuous", "numeric_discrete"):
            characterization["numeric_columns"].append(col)
        if t == "categorical" or t == "boolean":
            characterization["categorical_columns"].append(col)

    # Target detection
    for col in df.columns:
        if any(h in col.lower() for h in TARGET_HINTS):
            characterization["target_column"] = col
            break
    if not characterization["target_column"] and characterization["categorical_columns"]:
        # Prefer binary or few-class column as target
        for col in characterization["categorical_columns"]:
            n = df[col].nunique()
            if 2 <= n <= 10:
                characterization["target_column"] = col
                break

    target = characterization["target_column"]
    if target:
        t = column_types.get(target, "")
        if t in ("categorical", "boolean", "numeric_discrete") and df[target].nunique() <= 20:
            characterization["kind"] = "classification"
        elif t in ("numeric_continuous", "numeric_discrete"):
            characterization["kind"] = "regression"
    elif characterization["datetime_column"] and characterization["numeric_columns"]:
        characterization["kind"] = "time_series"
    elif characterization["numeric_columns"]:
        characterization["kind"] = "distribution"
    return characterization
