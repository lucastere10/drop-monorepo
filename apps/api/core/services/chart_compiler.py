from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.models import Analysis, ChartSpec
from core.services.chart_format import HISTOGRAM_DESCRIPTION, format_bin_label
from core.services.chart_selection import intent_allowed, pie_is_readable
from core.services.column_labels import present_chart_text
from core.services.pipeline import load_analysis_dataframe

_KIND_DESCRIPTION = {
    "categorical_top": "contagem das categorias mais frequentes",
    "histogram": HISTOGRAM_DESCRIPTION,
    "timeseries": "média diária ao longo do tempo",
    "groupby": "agregação por categoria",
    "correlation": "força da relação entre colunas numéricas",
}


def compile_intent(
    df: pd.DataFrame,
    summary: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any] | None:
    kind = intent.get("kind")
    columns = [str(c) for c in (intent.get("columns") or [])]
    agg = intent.get("agg") or "count"
    if not intent_allowed(str(kind), columns, summary, df):
        return None
    built: dict[str, Any] | None
    if kind == "categorical_top":
        built = _categorical(df, columns)
    elif kind == "histogram":
        built = _histogram(df, columns)
    elif kind == "timeseries":
        built = _timeseries(df, columns)
    elif kind == "groupby":
        built = _groupby(df, columns, str(agg))
    elif kind == "correlation":
        built = _correlation(df, summary, columns)
    else:
        return None
    if not built or not built["labels"] or sum(built["values"]) <= 0:
        return None

    title = str(intent.get("title") or built["title"])
    description = str(intent.get("description") or built["description"])
    title, description, axis_labels = present_chart_text(
        summary,
        title=title,
        description=description,
        kind=str(kind),
        labels=built["labels"],
    )
    requested = intent.get("chart_type")
    chart_type = requested if requested in {"bar", "line", "pie"} else built["chart_type"]
    if chart_type == "pie" and not pie_is_readable(built["values"]):
        chart_type = "bar"
    orientation = "vertical"
    if chart_type == "bar" and kind in {"categorical_top", "groupby"}:
        orientation = "horizontal"
    return {
        "title": title,
        "chart_type": chart_type,
        "spec": {
            "title": title,
            "description": description,
            "chart_type": chart_type,
            "labels": axis_labels,
            "values": built["values"],
            "source": "deterministic",
            "rule": kind,
            "columns": built["columns"],
            "agg": agg if kind == "groupby" else None,
            "value_label": _value_label(str(kind), str(agg)),
            "orientation": orientation,
        },
    }


def materialize_chart_intents(
    analysis: Analysis,
    intents: list[dict[str, Any]],
    *,
    source: str,
) -> list[ChartSpec]:
    if not intents:
        return []
    df = load_analysis_dataframe(analysis)
    summary = analysis.summary or {}
    created: list[ChartSpec] = []
    for intent in intents:
        payload = compile_intent(df, summary, intent)
        if payload is None:
            continue
        payload["spec"]["source"] = source
        created.append(
            ChartSpec.objects.create(
                analysis=analysis,
                title=payload["title"],
                chart_type=payload["chart_type"],
                spec=payload["spec"],
            )
        )
    return created


def _categorical(df: pd.DataFrame, columns: list[str]) -> dict[str, Any] | None:
    if len(columns) < 1 or columns[0] not in df.columns:
        return None
    col = columns[0]
    vc = df[col].dropna().astype(str).value_counts().head(10)
    if vc.empty:
        return None
    return {
        "title": f"Distribuição de {col}",
        "description": _KIND_DESCRIPTION["categorical_top"],
        "chart_type": "pie" if len(vc) <= 5 else "bar",
        "labels": [str(i)[:40] for i in vc.index.tolist()],
        "values": [float(v) for v in vc.tolist()],
        "columns": [col],
    }


def _histogram(df: pd.DataFrame, columns: list[str]) -> dict[str, Any] | None:
    if len(columns) < 1 or columns[0] not in df.columns:
        return None
    col = columns[0]
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(series) < 5:
        return None
    bins = min(10, max(5, int(np.sqrt(len(series)))))
    counts, edges = np.histogram(series.to_numpy(dtype=float), bins=bins)
    labels = [
        format_bin_label(float(edges[i]), float(edges[i + 1])) for i in range(len(counts))
    ]
    return {
        "title": f"Distribuição de {col}",
        "description": _KIND_DESCRIPTION["histogram"],
        "chart_type": "bar",
        "labels": labels,
        "values": [float(c) for c in counts],
        "columns": [col],
    }


def _timeseries(df: pd.DataFrame, columns: list[str]) -> dict[str, Any] | None:
    if len(columns) < 2 or columns[0] not in df.columns or columns[1] not in df.columns:
        return None
    dt_col, num_col = columns[0], columns[1]
    try:
        tmp = df[[dt_col, num_col]].copy()
        tmp[num_col] = pd.to_numeric(tmp[num_col], errors="coerce")
        tmp = tmp.dropna()
        if len(tmp) < 3:
            return None
        tmp["_period"] = pd.to_datetime(tmp[dt_col]).dt.to_period("D").astype(str)
        grouped = tmp.groupby("_period", sort=True)[num_col].mean().head(30)
    except (ValueError, TypeError, OverflowError):
        return None
    if len(grouped) < 3:
        return None
    return {
        "title": f"{num_col} ao longo do tempo",
        "description": _KIND_DESCRIPTION["timeseries"],
        "chart_type": "line",
        "labels": [str(i) for i in grouped.index.tolist()],
        "values": [float(v) for v in grouped.tolist()],
        "columns": [dt_col, num_col],
    }


def _groupby(df: pd.DataFrame, columns: list[str], agg: str) -> dict[str, Any] | None:
    if len(columns) < 1 or columns[0] not in df.columns:
        return None
    cat = columns[0]
    if agg == "count" or len(columns) < 2:
        vc = df[cat].dropna().astype(str).value_counts().head(12)
        if vc.empty:
            return None
        labels = [str(i)[:40] for i in vc.index.tolist()]
        values = [float(v) for v in vc.tolist()]
        description = "contagem por categoria"
    else:
        num = columns[1]
        if num not in df.columns:
            return None
        tmp = pd.DataFrame(
            {
                "_c": df[cat].astype(str),
                "_n": pd.to_numeric(df[num], errors="coerce"),
            }
        ).dropna(subset=["_n"])
        tmp = tmp[tmp["_c"].ne("nan")]
        if tmp.empty:
            return None
        fn = "mean" if agg == "mean" else "sum"
        grouped = tmp.groupby("_c")["_n"].agg(fn).sort_values(ascending=False).head(12)
        labels = [str(i)[:40] for i in grouped.index.tolist()]
        values = [float(v) for v in grouped.tolist()]
        description = "média por categoria" if fn == "mean" else "soma por categoria"
    if not labels:
        return None
    chart_type = "pie" if len(labels) <= 5 and agg == "count" else "bar"
    return {
        "title": f"{cat}",
        "description": description,
        "chart_type": chart_type,
        "labels": labels,
        "values": values,
        "columns": columns[:2],
    }


def _correlation(
    df: pd.DataFrame,
    summary: dict[str, Any],
    columns: list[str],
) -> dict[str, Any] | None:
    if len(columns) >= 2:
        a, b = columns[0], columns[1]
        if a not in df.columns or b not in df.columns:
            return None
        pair = df[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(pair) < 3:
            return None
        r = float(pair[a].corr(pair[b]))
        if np.isnan(r):
            return None
        return {
            "title": f"Correlação {a} × {b}",
            "description": _KIND_DESCRIPTION["correlation"],
            "chart_type": "bar",
            "labels": [f"{a}×{b}"[:40]],
            "values": [round(abs(r), 3)],
            "columns": [a, b],
        }
    corr = summary.get("correlations") or {}
    pairs: list[tuple[float, str, str]] = []
    for key, val in corr.items():
        if "|" not in str(key):
            continue
        left, right = str(key).split("|", 1)
        try:
            r = float(val)
        except (TypeError, ValueError):
            continue
        pairs.append((abs(r), left, right))
    pairs.sort(reverse=True)
    top = pairs[:5]
    if len(top) < 2:
        return None
    return {
        "title": "Correlações mais fortes",
        "description": _KIND_DESCRIPTION["correlation"],
        "chart_type": "bar",
        "labels": [f"{a}×{b}"[:40] for _, a, b in top],
        "values": [round(abs_r, 3) for abs_r, _, _ in top],
        "columns": [c for _, a, b in top for c in (a, b)],
    }


def _value_label(kind: str, agg: str) -> str:
    if kind == "timeseries":
        return "média"
    if kind == "correlation":
        return "correlação"
    if kind == "groupby" and agg == "mean":
        return "média"
    if kind == "groupby" and agg == "sum":
        return "soma"
    return "frequência"
