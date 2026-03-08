"""Auto-analyze DataFrame(s): type detection, metric selection, explainability."""
from typing import Any, Dict, List, Optional

import pandas as pd

from .metrics import compute_metrics, get_explainability_messages
from .types import detect_column_types, characterize_dataset


def run_analysis(dfs: List[pd.DataFrame]) -> Dict[str, Any]:
    """
    Run full analysis on a list of DataFrames.
    Uses the first non-empty DataFrame as primary; others can be summarized.
    """
    if not dfs:
        return {
            "error": "No data",
            "columns": [],
            "dataset_level": {},
            "explainability": [],
            "data_profile": [],
        }
    df = dfs[0]
    if df.empty:
        return {
            "error": "Empty dataset",
            "columns": [],
            "dataset_level": {},
            "explainability": [],
            "data_profile": [],
        }

    # Per-column type detection
    column_types = detect_column_types(df)
    # Dataset-level characterization
    characterization = characterize_dataset(df, column_types)
    # Metrics and explainability
    metrics_result = compute_metrics(df, column_types, characterization)
    explainability = get_explainability_messages(characterization, metrics_result)

    # Build per-column profile (type, sample stats, percentiles where applicable)
    data_profile: List[Dict[str, Any]] = []
    for col in df.columns:
        ctype = column_types.get(col, "unknown")
        entry: Dict[str, Any] = {
            "column": col,
            "type": ctype,
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum()),
        }
        s = df[col].dropna()
        if ctype in ("numeric_continuous", "numeric_discrete") and len(s) > 0:
            try:
                num = pd.to_numeric(s, errors="coerce").dropna()
                if len(num) > 0:
                    entry["min"] = float(num.min())
                    entry["max"] = float(num.max())
                    entry["mean"] = float(num.mean())
                    entry["p25"] = float(num.quantile(0.25))
                    entry["p50"] = float(num.quantile(0.50))
                    entry["p75"] = float(num.quantile(0.75))
                    entry["std"] = float(num.std()) if len(num) > 1 else 0.0
            except Exception:
                pass
        elif ctype == "categorical" and len(s) > 0:
            vc = s.astype(str).value_counts()
            entry["unique_count"] = len(vc)
            entry["top_values"] = vc.head(5).to_dict()
        elif ctype == "datetime" and len(s) > 0:
            try:
                d = pd.to_datetime(s, errors="coerce").dropna()
                if len(d) > 0:
                    entry["min_date"] = str(d.min())
                    entry["max_date"] = str(d.max())
            except Exception:
                pass
        data_profile.append(entry)

    return {
        "error": None,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "column_types": column_types,
        "data_profile": data_profile,
        "dataset_level": {
            "characterization": characterization,
            "metrics": metrics_result.get("metrics", {}),
            "metric_names": metrics_result.get("metric_names", []),
        },
        "explainability": explainability,
        "sheet_count": len(dfs),
    }
