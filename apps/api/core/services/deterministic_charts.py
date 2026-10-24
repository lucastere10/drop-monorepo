from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.models import Analysis, ChartSpec
from core.services.chart_format import HISTOGRAM_DESCRIPTION, format_bin_label
from core.services.chart_selection import HARD_CAP, select_chart_slots
from core.services.dashboard_layout import build_dashboard_layout

MAX_CHARTS = HARD_CAP

RULE_DESCRIPTIONS = {
    "missingness": "percentual de valores ausentes por coluna",
    "categorical_top_n": "contagem das categorias mais frequentes",
    "numeric_histogram": HISTOGRAM_DESCRIPTION,
    "datetime_line": "média diária ao longo do tempo",
}

VALUE_LABELS = {
    "missingness": "ausência (%)",
    "categorical_top_n": "frequência",
    "numeric_histogram": "frequência",
    "datetime_line": "média",
}


def build_deterministic_chart_specs(
    df: pd.DataFrame,
    summary: dict[str, Any],
    *,
    max_charts: int = MAX_CHARTS,
) -> list[dict[str, Any]]:
    """Build chart payloads from the selection quotas and real dataframe values."""
    slots = select_chart_slots(summary, datetime_columns=_datetime_columns(df))
    specs: list[dict[str, Any]] = []
    for slot in slots:
        if len(specs) >= max_charts:
            break
        payload = _materialize(df, summary, slot)
        if payload:
            specs.append(payload)
    return specs


def save_deterministic_charts(
    analysis: Analysis,
    df: pd.DataFrame,
    *,
    summary: dict[str, Any] | None = None,
) -> list[ChartSpec]:
    raw = summary if summary is not None else (analysis.summary or {})
    payloads = build_deterministic_chart_specs(df, raw)
    created: list[ChartSpec] = []
    for payload in payloads:
        created.append(
            ChartSpec.objects.create(
                analysis=analysis,
                title=payload["title"],
                chart_type=payload["chart_type"],
                spec=payload["spec"],
            )
        )
    analysis.dashboard_layout = build_dashboard_layout(
        [(str(chart.id), chart.chart_type) for chart in created]
    )
    analysis.save(update_fields=["dashboard_layout", "updated_at"])
    return created


def _materialize(
    df: pd.DataFrame,
    summary: dict[str, Any],
    slot: dict[str, Any],
) -> dict[str, Any] | None:
    rule = slot["rule"]
    if rule == "missingness":
        return _missingness(summary, slot)
    if rule == "categorical_top_n":
        return _categorical(summary, slot)
    if rule == "numeric_histogram":
        return _histogram(df, slot)
    if rule == "datetime_line":
        return _timeseries(df, slot)
    return None


def _missingness(summary: dict[str, Any], slot: dict[str, Any]) -> dict[str, Any] | None:
    schema = {c["name"]: c for c in (summary.get("schema") or []) if c.get("name")}
    labels: list[str] = []
    values: list[float] = []
    for col in slot["columns"]:
        meta = schema.get(col) or {}
        try:
            pct = float(meta.get("null_pct") or 0)
        except (TypeError, ValueError):
            continue
        if pct <= 0:
            continue
        labels.append(str(col)[:40])
        values.append(round(pct, 2))
    if not labels:
        return None
    return _payload(
        title="Valores ausentes",
        description=RULE_DESCRIPTIONS["missingness"],
        chart_type="bar",
        labels=labels,
        values=values,
        rule="missingness",
        columns=list(slot["columns"]),
        orientation="horizontal",
    )


def _categorical(summary: dict[str, Any], slot: dict[str, Any]) -> dict[str, Any] | None:
    col = slot["columns"][0]
    rows = (summary.get("categorical_top") or {}).get(col) or []
    if not isinstance(rows, list):
        return None
    labels = [str(row.get("value", ""))[:40] for row in rows[:12]]
    values = [float(row.get("count") or 0) for row in rows[:12]]
    if sum(values) <= 0:
        return None
    return _payload(
        title=f"Distribuição de {col}",
        chart_type=slot["chart_type"],
        labels=labels,
        values=values,
        rule="categorical_top_n",
        columns=[col],
        orientation=slot.get("orientation") or "horizontal",
    )


def _histogram(df: pd.DataFrame, slot: dict[str, Any]) -> dict[str, Any] | None:
    col = slot["columns"][0]
    if col not in df.columns:
        return None
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(series) < 5:
        return None
    bins = min(10, max(5, int(np.sqrt(len(series)))))
    counts, edges = np.histogram(series.to_numpy(dtype=float), bins=bins)
    labels = [format_bin_label(float(edges[i]), float(edges[i + 1])) for i in range(len(counts))]
    values = [float(count) for count in counts]
    if sum(values) <= 0:
        return None
    return _payload(
        title=f"Distribuição de {col}",
        chart_type="bar",
        labels=labels,
        values=values,
        rule="numeric_histogram",
        columns=[col],
        orientation="vertical",
    )


def _timeseries(df: pd.DataFrame, slot: dict[str, Any]) -> dict[str, Any] | None:
    numeric = slot["columns"][-1]
    dates = [slot["columns"][0], *_datetime_columns(df)]
    seen: set[str] = set()
    for dt_col in dates:
        if dt_col in seen or dt_col not in df.columns or numeric not in df.columns:
            continue
        seen.add(dt_col)
        built = _daily_mean(df, dt_col, numeric)
        if built:
            labels, values = built
            return _payload(
                title=f"{numeric} ao longo do tempo",
                chart_type="line",
                labels=labels,
                values=values,
                rule="datetime_line",
                columns=[dt_col, numeric],
                orientation="vertical",
            )
    return None


def _daily_mean(
    df: pd.DataFrame,
    dt_col: str,
    numeric: str,
) -> tuple[list[str], list[float]] | None:
    try:
        tmp = df[[dt_col, numeric]].copy()
        tmp[numeric] = pd.to_numeric(tmp[numeric], errors="coerce")
        tmp = tmp.dropna()
        if len(tmp) < 3:
            return None
        tmp["_period"] = pd.to_datetime(tmp[dt_col]).dt.to_period("D").astype(str)
        grouped = tmp.groupby("_period", sort=True)[numeric].mean().head(30)
    except (ValueError, TypeError, OverflowError):
        return None
    if len(grouped) < 3:
        return None
    labels = [str(item) for item in grouped.index.tolist()]
    values = [float(item) for item in grouped.tolist()]
    return labels, values


def _datetime_columns(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    return [
        str(col)
        for col in df.columns
        if str(df[col].dtype).startswith("datetime") or pd.api.types.is_datetime64_any_dtype(df[col])
    ]


def _payload(
    *,
    title: str,
    chart_type: str,
    labels: list[str],
    values: list[float],
    rule: str,
    columns: list[str],
    orientation: str,
    description: str = "",
) -> dict[str, Any]:
    desc = description or RULE_DESCRIPTIONS.get(rule, "")
    return {
        "title": title[:200],
        "chart_type": chart_type,
        "spec": {
            "title": title,
            "description": desc,
            "chart_type": chart_type,
            "labels": labels,
            "values": values,
            "source": "deterministic",
            "rule": rule,
            "columns": columns,
            "value_label": VALUE_LABELS.get(rule, "frequência"),
            "orientation": orientation,
        },
    }
