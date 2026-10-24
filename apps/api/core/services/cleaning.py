from __future__ import annotations

from typing import Any

import pandas as pd


BOOL_MAP = {
    "sim": True,
    "não": False,
    "nao": False,
    "yes": True,
    "no": False,
    "true": True,
    "false": False,
    "1": True,
    "0": False,
}


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Light deterministic cleaning. Returns (cleaned_df, cleaning_report)."""
    rows_before = int(len(df))
    cols_before = list(df.columns)
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    # Deduplicate column names
    seen: dict[str, int] = {}
    new_cols = []
    for c in out.columns:
        if c not in seen:
            seen[c] = 0
            new_cols.append(c)
        else:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
    out.columns = new_cols

    empty_cols = [c for c in out.columns if out[c].isna().all()]
    out = out.dropna(axis=1, how="all")

    dtypes_changed: dict[str, str] = {}
    for col in list(out.columns):
        series = out[col]
        if series.dtype == object:
            stripped = series.apply(lambda x: x.strip() if isinstance(x, str) else x)
            out[col] = stripped
            # percent strings → float
            sample = stripped.dropna().astype(str).head(20)
            if len(sample) and sample.str.endswith("%").mean() > 0.8:
                converted = (
                    stripped.astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                numeric = pd.to_numeric(converted, errors="coerce")
                if numeric.notna().sum() >= max(1, int(0.5 * stripped.notna().sum())):
                    out[col] = numeric
                    dtypes_changed[str(col)] = "float_percent"
                    continue
            # bool-like
            lower = stripped.dropna().astype(str).str.lower().str.strip()
            if len(lower) and lower.isin(BOOL_MAP.keys()).mean() > 0.9:
                out[col] = stripped.astype(str).str.lower().str.strip().map(BOOL_MAP)
                dtypes_changed[str(col)] = "bool"
                continue
            # numeric-like
            numeric = pd.to_numeric(
                stripped.astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )
            if numeric.notna().sum() >= max(1, int(0.8 * stripped.notna().sum())):
                out[col] = numeric
                dtypes_changed[str(col)] = "numeric"
                continue
            # dates (conservative)
            if _looks_like_dates(stripped):
                parsed = pd.to_datetime(stripped, errors="coerce", utc=False)
                if parsed.notna().sum() >= max(1, int(0.8 * stripped.notna().sum())):
                    out[col] = parsed
                    dtypes_changed[str(col)] = "datetime"

    report = {
        "rows_before": rows_before,
        "rows_after": int(len(out)),
        "cols_before": len(cols_before),
        "cols_after": int(out.shape[1]),
        "columns_dropped": [str(c) for c in empty_cols],
        "dtypes_changed": dtypes_changed,
        "duplicates_reported_only": True,
    }
    return out, report


def _looks_like_dates(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(15)
    if len(sample) < 3:
        return False
    # crude ISO / BR date hint
    pattern = sample.str.contains(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", regex=True)
    return bool(pattern.mean() > 0.8)
