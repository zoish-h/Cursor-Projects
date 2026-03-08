"""Compute metrics and explainability messages based on data type."""
from typing import Any, Dict, List

import pandas as pd


def compute_metrics(
    df: pd.DataFrame,
    column_types: Dict[str, str],
    characterization: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute metrics based on dataset characterization.
    Returns dict with 'metrics' (name -> value) and 'metric_names' (ordered list).
    """
    metrics: Dict[str, Any] = {}
    metric_names: List[str] = []
    kind = characterization.get("kind", "generic")
    target = characterization.get("target_column")
    numeric_cols = characterization.get("numeric_columns", [])

    if kind == "classification" and target and target in df.columns:
        s = df[target].dropna().astype(str)
        if len(s) > 0:
            vc = s.value_counts()
            total = len(s)
            # Accuracy: use majority class as "predicted" for lack of predictions
            majority_pct = vc.iloc[0] / total if total else 0
            metrics["accuracy_baseline_majority"] = round(majority_pct, 4)
            metrics["class_distribution"] = vc.to_dict()
            metrics["num_classes"] = len(vc)
            metric_names = ["accuracy_baseline_majority", "num_classes"]
        metrics["explanation_type"] = "classification"

    elif kind == "regression" and target and target in df.columns:
        try:
            y = pd.to_numeric(df[target], errors="coerce").dropna()
            if len(y) > 0:
                metrics["mean"] = round(float(y.mean()), 4)
                metrics["std"] = round(float(y.std()), 4) if len(y) > 1 else 0.0
                metrics["rmse_baseline_mean"] = round(float(((y - y.mean()) ** 2).mean() ** 0.5), 4)
                metrics["mae_baseline_median"] = round(float((y - y.median()).abs().mean()), 4)
                metrics["p25"] = round(float(y.quantile(0.25)), 4)
                metrics["p50"] = round(float(y.quantile(0.50)), 4)
                metrics["p75"] = round(float(y.quantile(0.75)), 4)
                metric_names = ["mean", "std", "rmse_baseline_mean", "mae_baseline_median", "p25", "p50", "p75"]
        except Exception:
            pass
        metrics["explanation_type"] = "regression"

    elif kind == "time_series":
        dt_col = characterization.get("datetime_column")
        if dt_col and dt_col in df.columns and numeric_cols:
            try:
                d = pd.to_datetime(df[dt_col], errors="coerce").dropna()
                if len(d) > 1:
                    metrics["date_range_start"] = str(d.min())
                    metrics["date_range_end"] = str(d.max())
                    metrics["period_count"] = len(d)
                for nc in numeric_cols[:3]:
                    num = pd.to_numeric(df[nc], errors="coerce").dropna()
                    if len(num) > 1:
                        metrics[f"{nc}_mean"] = round(float(num.mean()), 4)
                        metrics[f"{nc}_trend_hint"] = "increasing" if num.iloc[-1] > num.iloc[0] else "decreasing or flat"
            except Exception:
                pass
            metric_names = [k for k in metrics if k != "explanation_type"]
        metrics["explanation_type"] = "time_series"

    else:
        # Distribution / generic: percentiles and summary for numeric columns
        for col in numeric_cols[:10]:
            try:
                num = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(num) > 0:
                    metrics[f"{col}_mean"] = round(float(num.mean()), 4)
                    metrics[f"{col}_p25"] = round(float(num.quantile(0.25)), 4)
                    metrics[f"{col}_p50"] = round(float(num.quantile(0.50)), 4)
                    metrics[f"{col}_p75"] = round(float(num.quantile(0.75)), 4)
                    metrics[f"{col}_min"] = round(float(num.min()), 4)
                    metrics[f"{col}_max"] = round(float(num.max()), 4)
            except Exception:
                pass
        if not metric_names:
            metric_names = [k for k in metrics.keys()]
        metrics["explanation_type"] = "distribution"

    return {"metrics": metrics, "metric_names": metric_names}


def get_explainability_messages(
    characterization: Dict[str, Any],
    metrics_result: Dict[str, Any],
) -> List[str]:
    """Return human-readable explainability messages for why these metrics were chosen."""
    messages: List[str] = []
    kind = characterization.get("kind", "generic")
    exp_type = metrics_result.get("metrics", {}).get("explanation_type", "")

    if kind == "classification" or exp_type == "classification":
        messages.append(
            "Categorical or binary target detected; classification metrics chosen (e.g. accuracy baseline, class distribution)."
        )
    elif kind == "regression" or exp_type == "regression":
        messages.append(
            "Continuous target detected; regression-style metrics chosen (mean, std, RMSE/MAE baselines, percentiles)."
        )
    elif kind == "time_series" or exp_type == "time_series":
        messages.append(
            "Time series detected; date range and trend hints included. Consider period stats for seasonality."
        )
    else:
        messages.append(
            "Numeric data without a single target; distribution and percentiles reported for each numeric column."
        )
    return messages
