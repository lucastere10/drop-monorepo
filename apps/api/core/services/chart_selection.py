from __future__ import annotations

from typing import Any

import pandas as pd

NULL_PCT_MAX = 60.0
NULL_FLOOR = 5.0
MAX_RANKED_CATEGORIES = 12
MAX_CATEGORY_CHARTS = 2
MAX_HISTOGRAMS = 2
MAX_MISSING_COLUMNS = 12
HARD_CAP = 8
PIE_SHARE_MAX = 0.85


def select_chart_slots(
    summary: dict[str, Any],
    *,
    datetime_columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Quota of chart slots from profile metadata. No LLM and no dataframe."""
    schema = _schema(summary)
    n_rows = int(summary.get("n_rows") or 0)
    blocked = _missing_columns(schema)
    slots: list[dict[str, Any]] = []
    if blocked:
        slots.append(
            {
                "rule": "missingness",
                "columns": blocked,
                "chart_type": "bar",
                "orientation": "horizontal",
            }
        )
    blocked_set = set(blocked)
    slots.extend(_category_slots(summary, schema, blocked_set))
    histograms = _histogram_slots(summary, schema, n_rows, blocked_set)
    slots.extend(histograms)
    line = _line_slot(
        summary,
        schema,
        n_rows,
        blocked_set,
        [slot["columns"][0] for slot in histograms],
        datetime_columns or [],
    )
    if line:
        slots.append(line)
    return slots[:HARD_CAP]


def is_identifier(
    col: str,
    schema_by_name: dict[str, Any],
    n_rows: int,
    stats: dict[str, Any],
) -> bool:
    name = str(col).strip().lower()
    if name == "id" or name.endswith("_id"):
        return True
    meta = schema_by_name.get(col) or {}
    try:
        n_unique = int(meta["n_unique"])
        low = float(stats["min"])
        high = float(stats["max"])
    except (KeyError, TypeError, ValueError):
        return False
    if n_rows < 5 or n_unique < n_rows * 0.95:
        return False
    if not _is_whole(low) or not _is_whole(high):
        return False
    span = high - low + 1
    return span <= max(n_unique, 1) * 1.05


def relative_spread(stats: dict[str, Any]) -> float | None:
    try:
        std = abs(float(stats["std"]))
    except (KeyError, TypeError, ValueError):
        return None
    if std == 0:
        return None
    try:
        mean = abs(float(stats.get("mean") or 0))
    except (TypeError, ValueError):
        mean = 0.0
    return std / max(mean, 1.0)


def pie_is_readable(counts: list[float]) -> bool:
    if not (2 <= len(counts) <= 3):
        return False
    total = sum(counts)
    if total <= 0:
        return False
    return max(counts) / total <= PIE_SHARE_MAX


def intent_allowed(
    kind: str,
    columns: list[str],
    summary: dict[str, Any],
    df,
) -> bool:
    if kind == "correlation" or not columns:
        return False
    if kind in {"categorical_top", "groupby"}:
        return _category_allowed(columns, df) and _extra_numeric_allowed(kind, columns, summary, df)
    if kind == "histogram":
        return _histogram_allowed(columns[0], summary, df)
    if kind == "timeseries":
        return _timeseries_allowed(columns, summary, df)
    return False


def _schema(summary: dict[str, Any]) -> dict[str, Any]:
    return {c["name"]: c for c in (summary.get("schema") or []) if c.get("name")}


def _null_pct(meta: dict[str, Any]) -> float:
    try:
        return float(meta.get("null_pct") or 0)
    except (TypeError, ValueError):
        return 0.0


def _missing_columns(schema: dict[str, Any]) -> list[str]:
    ranked = [
        (_null_pct(meta), name)
        for name, meta in schema.items()
        if _null_pct(meta) >= NULL_FLOOR
    ]
    ranked.sort(reverse=True)
    return [name for _, name in ranked[:MAX_MISSING_COLUMNS]]


def _category_slots(
    summary: dict[str, Any],
    schema: dict[str, Any],
    blocked: set[str],
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    categorical = summary.get("categorical_top") or {}
    for col, rows in categorical.items():
        if len(slots) >= MAX_CATEGORY_CHARTS:
            break
        if col in blocked or not isinstance(rows, list):
            continue
        meta = schema.get(col) or {}
        if _null_pct(meta) > NULL_PCT_MAX:
            continue
        n_unique = _meta_unique(meta, rows)
        if n_unique < 2 or n_unique > MAX_RANKED_CATEGORIES:
            continue
        counts = [float(row.get("count") or 0) for row in rows[:MAX_RANKED_CATEGORIES]]
        if sum(counts) <= 0:
            continue
        pie = pie_is_readable(counts) and n_unique <= 3
        slots.append(
            {
                "rule": "categorical_top_n",
                "columns": [col],
                "chart_type": "pie" if pie else "bar",
                "orientation": "vertical" if pie else "horizontal",
            }
        )
    return slots


def _histogram_slots(
    summary: dict[str, Any],
    schema: dict[str, Any],
    n_rows: int,
    blocked: set[str],
) -> list[dict[str, Any]]:
    ranked = _ranked_numerics(summary, schema, n_rows, blocked)
    return [
        {
            "rule": "numeric_histogram",
            "columns": [col],
            "chart_type": "bar",
            "orientation": "vertical",
        }
        for col in ranked[:MAX_HISTOGRAMS]
    ]


def _line_slot(
    summary: dict[str, Any],
    schema: dict[str, Any],
    n_rows: int,
    blocked: set[str],
    histogram_cols: list[str],
    datetime_columns: list[str],
) -> dict[str, Any] | None:
    dates = [col for col in datetime_columns if _null_pct(schema.get(col) or {}) <= NULL_PCT_MAX]
    if not dates:
        return None
    ranked = _ranked_numerics(summary, schema, n_rows, blocked)
    fresh = [col for col in ranked if col not in histogram_cols]
    numeric = fresh[0] if fresh else (ranked[0] if ranked else None)
    if numeric is None:
        return None
    return {
        "rule": "datetime_line",
        "columns": [dates[0], numeric],
        "chart_type": "line",
        "orientation": "vertical",
    }


def _ranked_numerics(
    summary: dict[str, Any],
    schema: dict[str, Any],
    n_rows: int,
    blocked: set[str],
) -> list[str]:
    scored: list[tuple[float, str]] = []
    for col, stats in (summary.get("numeric_stats") or {}).items():
        if col in blocked or not isinstance(stats, dict):
            continue
        if _null_pct(schema.get(col) or {}) > NULL_PCT_MAX:
            continue
        if is_identifier(col, schema, n_rows, stats):
            continue
        try:
            count = int(stats.get("count") or 0)
        except (TypeError, ValueError):
            continue
        spread = relative_spread(stats)
        if count < 5 or spread is None:
            continue
        scored.append((spread, col))
    scored.sort(reverse=True)
    return [col for _, col in scored]


def _meta_unique(meta: dict[str, Any], rows: list) -> int:
    try:
        return int(meta["n_unique"])
    except (KeyError, TypeError, ValueError):
        return len(rows)


def _is_whole(value: float) -> bool:
    return abs(value - round(value)) <= 1e-6 * max(1.0, abs(value))


def _category_allowed(columns: list[str], df) -> bool:
    col = columns[0]
    if col not in df.columns:
        return False
    if _frame_null_pct(df, col) > NULL_PCT_MAX:
        return False
    n_unique = int(df[col].nunique(dropna=True))
    return 2 <= n_unique <= MAX_RANKED_CATEGORIES


def _extra_numeric_allowed(kind: str, columns: list[str], summary: dict[str, Any], df) -> bool:
    if kind != "groupby" or len(columns) < 2:
        return True
    return _numeric_column_ok(columns[1], summary, df, require_spread=False)


def _histogram_allowed(col: str, summary: dict[str, Any], df) -> bool:
    return _numeric_column_ok(col, summary, df, require_spread=True)


def _timeseries_allowed(columns: list[str], summary: dict[str, Any], df) -> bool:
    if len(columns) < 2 or columns[0] not in df.columns:
        return False
    if _frame_null_pct(df, columns[0]) > NULL_PCT_MAX:
        return False
    return _numeric_column_ok(columns[1], summary, df, require_spread=False)


def _numeric_column_ok(col: str, summary: dict[str, Any], df, *, require_spread: bool) -> bool:
    if col not in df.columns:
        return False
    if _frame_null_pct(df, col) > NULL_PCT_MAX:
        return False
    stats = _stats_for(col, summary, df)
    n_rows = int(summary.get("n_rows") or len(df))
    if is_identifier(col, _schema(summary), n_rows, stats):
        return False
    if not require_spread:
        return True
    try:
        count = int(stats.get("count") or 0)
    except (TypeError, ValueError):
        return False
    return count >= 5 and relative_spread(stats) is not None


def _stats_for(col: str, summary: dict[str, Any], df) -> dict[str, Any]:
    raw = (summary.get("numeric_stats") or {}).get(col)
    if isinstance(raw, dict) and raw.get("min") is not None and raw.get("max") is not None:
        return raw
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    if series.empty:
        return {}
    std = float(series.std()) if len(series) > 1 else None
    return {
        "count": int(series.count()),
        "std": std,
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
    }


def _frame_null_pct(df, col: str) -> float:
    n_rows = len(df)
    if n_rows == 0:
        return 0.0
    return float(df[col].isna().mean() * 100)
