from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def profile_dataframe(
    df: pd.DataFrame,
    *,
    sample_rows: int = 50,
    cleaning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    n_rows, n_cols = df.shape
    schema = []
    for col in df.columns:
        series = df[col]
        null_pct = float(series.isna().mean() * 100) if n_rows else 0.0
        example = None
        non_null = series.dropna()
        if len(non_null):
            example = non_null.iloc[0]
            if isinstance(example, (np.generic,)):
                example = example.item()
            elif hasattr(example, "isoformat"):
                example = example.isoformat()
            example = str(example)[:200]
        schema.append(
            {
                "name": str(col),
                "dtype": str(series.dtype),
                "null_pct": round(null_pct, 2),
                "n_unique": int(series.nunique(dropna=True)),
                "example": example,
            }
        )

    missing = {str(c): int(df[c].isna().sum()) for c in df.columns}

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_stats: dict[str, Any] = {}
    for col in numeric_cols[:40]:
        s = df[col]
        desc = s.describe()
        numeric_stats[str(col)] = {
            "count": int(desc.get("count", 0)),
            "min": _safe_float(desc.get("min")),
            "max": _safe_float(desc.get("max")),
            "mean": _safe_float(desc.get("mean")),
            "std": _safe_float(desc.get("std")),
            "p25": _safe_float(desc.get("25%")),
            "p50": _safe_float(desc.get("50%")),
            "p75": _safe_float(desc.get("75%")),
        }

    categorical: dict[str, Any] = {}
    for col in df.columns:
        if col in numeric_cols:
            continue
        if str(df[col].dtype).startswith("datetime"):
            continue
        nunique = int(df[col].nunique(dropna=True))
        if nunique > 50:
            continue
        vc = df[col].astype(str).value_counts().head(12)
        categorical[str(col)] = [{"value": k, "count": int(v)} for k, v in vc.items()]
        if len(categorical) >= 20:
            break

    corr: dict[str, float] = {}
    if len(numeric_cols) >= 2:
        subset = numeric_cols[:15]
        corr_df = df[subset].corr(numeric_only=True)
        pairs: list[tuple[float, str, str]] = []
        for i, a in enumerate(corr_df.columns):
            for b in corr_df.columns[i + 1 :]:
                val = _safe_float(corr_df.loc[a, b])
                if val is None:
                    continue
                pairs.append((abs(val), str(a), str(b)))
        pairs.sort(reverse=True)
        for _abs, a, b in pairs[:20]:
            val = _safe_float(corr_df.loc[a, b])
            if val is not None:
                corr[f"{a}|{b}"] = val

    outliers = detect_outliers(df)
    duplicates = detect_duplicates(df)
    quality = calculate_quality_score(df, outliers=outliers, duplicates=duplicates)

    sample = df.head(sample_rows).astype(object).where(pd.notnull(df.head(sample_rows)), None)
    sample_records = sample.to_dict(orient="records")
    for row in sample_records:
        for k, v in list(row.items()):
            if isinstance(v, (np.generic,)):
                row[k] = v.item()
            elif hasattr(v, "isoformat"):
                row[k] = v.isoformat()

    missing_total = int(sum(missing.values()))
    cells = max(n_rows * n_cols, 1)

    return {
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "schema": schema,
        "missing": missing,
        "missing_total": missing_total,
        "missing_pct": round(missing_total / cells * 100, 2),
        "numeric_stats": numeric_stats,
        "categorical_top": categorical,
        "correlations": corr,
        "outliers": outliers,
        "duplicates": duplicates,
        "quality": quality,
        "quality_score": quality["score"],
        "quality_grade": quality["grade"],
        "cleaning": cleaning or {},
        "sample_rows": sample_records,
        "text_summary": generate_text_summary(
            n_rows=n_rows,
            n_cols=n_cols,
            quality=quality,
            missing_pct=round(missing_total / cells * 100, 2),
            duplicates=duplicates,
            outliers=outliers,
        ),
    }


def detect_outliers(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    outliers: dict[str, dict[str, Any]] = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (df[col] < lower) | (df[col] > upper)
        count = int(mask.sum())
        if count > 0:
            outliers[str(col)] = {
                "count": count,
                "percentage": round(count / max(len(df), 1) * 100, 2),
                "lower_bound": _safe_float(lower),
                "upper_bound": _safe_float(upper),
            }
    return outliers


def detect_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    dup_count = int(df.duplicated().sum())
    return {
        "has_duplicates": dup_count > 0,
        "count": dup_count,
        "percentage": round(dup_count / max(len(df), 1) * 100, 2),
    }


def calculate_quality_score(
    df: pd.DataFrame,
    *,
    outliers: dict[str, dict[str, Any]],
    duplicates: dict[str, Any],
) -> dict[str, Any]:
    n_rows, n_cols = df.shape
    total_cells = max(n_rows * n_cols, 1)
    missing_cells = int(df.isna().sum().sum())
    completeness = (total_cells - missing_cells) / total_cells * 100
    uniqueness = 100 - float(duplicates.get("percentage") or 0)
    total_outliers = sum(info.get("count", 0) for info in outliers.values())
    numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
    outlier_pct = (
        (total_outliers / (n_rows * numeric_cols) * 100)
        if numeric_cols > 0 and n_rows > 0
        else 0.0
    )
    consistency = max(0.0, 100 - outlier_pct * 2)
    components = {
        "completeness": round(completeness, 2),
        "uniqueness": round(uniqueness, 2),
        "consistency": round(consistency, 2),
    }
    final = components["completeness"] * 0.4 + components["uniqueness"] * 0.3 + components["consistency"] * 0.3
    if final >= 95:
        grade = "S"
    elif final >= 85:
        grade = "A"
    elif final >= 75:
        grade = "B"
    elif final >= 60:
        grade = "C"
    elif final >= 40:
        grade = "D"
    else:
        grade = "F"
    return {
        "score": round(final, 2),
        "grade": grade,
        "components": components,
        "recommendations": _quality_recommendations(components),
    }


def generate_text_summary(
    *,
    n_rows: int,
    n_cols: int,
    quality: dict[str, Any],
    missing_pct: float,
    duplicates: dict[str, Any],
    outliers: dict[str, dict[str, Any]],
) -> str:
    grade = quality.get("grade", "?")
    score = quality.get("score", 0)
    lines = [
        f"Dataset com {n_rows} linhas e {n_cols} colunas.",
        f"Nota de qualidade: {grade} ({score}/100).",
        f"Valores ausentes: {missing_pct}% das células.",
    ]
    if duplicates.get("has_duplicates"):
        lines.append(
            f"Duplicatas: {duplicates.get('count')} linhas ({duplicates.get('percentage')}%)."
        )
    if outliers:
        top = sorted(outliers.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:3]
        parts = [f"{k} ({v['count']})" for k, v in top]
        lines.append("Outliers (IQR) em: " + ", ".join(parts) + ".")
    lines.extend((quality.get("recommendations") or [])[:2])
    return " ".join(lines)


def _quality_recommendations(scores: dict[str, float]) -> list[str]:
    recs: list[str] = []
    if scores.get("completeness", 100) < 90:
        recs.append("Trate valores faltantes antes de análises avançadas.")
    if scores.get("uniqueness", 100) < 95:
        recs.append("Há registros duplicados que podem enviesar resultados.")
    if scores.get("consistency", 100) < 80:
        recs.append("Muitos outliers — verifique se são erros ou valores válidos.")
    if not recs:
        recs.append("Dataset com boa qualidade para exploração.")
    return recs


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:  # noqa: BLE001
        return None
