from __future__ import annotations

import json
from typing import Any

from core.models import Analysis

KINDS = {"categorical_top", "histogram", "timeseries", "groupby", "correlation"}
CHART_TYPES = {"bar", "line", "pie"}
AGGS = {"count", "mean", "sum"}

def _plan_system(min_charts: int, max_charts: int) -> str:
    return (
        "Você escolhe gráficos para um dashboard de dados tabulares. "
        "Responda APENAS JSON válido no formato "
        '{"charts": [{"title": str, "description": str, '
        '"chart_type": "bar"|"line"|"pie", '
        '"kind": "categorical_top"|"histogram"|"timeseries"|"groupby"|"correlation", '
        '"columns": [str], "agg": "count"|"mean"|"sum"|null}]}. '
        f"Devolva entre {min_charts} e {max_charts} gráficos. "
        "Use somente colunas presentes no contexto. Não invente colunas. "
        "Não inclua labels nem values — o servidor calcula os números. "
        "title é uma frase curta em português (ex.: Pedidos por região). "
        "Se column_labels trouxer um rótulo para a coluna, use esse rótulo no title "
        "e na description. O campo columns continua com o nome original. "
        "Não deixe snake_case no título. "
        "description explica a métrica em uma linha. "
        "categorical_top e histogram usam 1 coluna. "
        "timeseries usa [data, numérica]. "
        "groupby usa [categoria] com agg count, ou [categoria, numérica] com mean ou sum. "
        "correlation usa duas colunas numéricas. "
        "Prefira gráficos que um gestor entenderia. Varie os tipos."
    )


def normalize_intent(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind") or "")
    if kind not in KINDS:
        return None
    columns = [str(c).strip() for c in (raw.get("columns") or []) if str(c).strip()][:3]
    chart_type = raw.get("chart_type") if raw.get("chart_type") in CHART_TYPES else "bar"
    agg = raw.get("agg") if raw.get("agg") in AGGS else "count"
    return {
        "title": str(raw.get("title") or "")[:200],
        "description": str(raw.get("description") or "")[:300],
        "chart_type": chart_type,
        "kind": kind,
        "columns": columns,
        "agg": agg,
    }


def parse_intent_list(content: str) -> list[dict[str, Any]]:
    data = json.loads(content)
    if isinstance(data, dict) and isinstance(data.get("charts"), list):
        raw_list = data["charts"]
    elif isinstance(data, dict) and data.get("kind"):
        raw_list = [data]
    elif isinstance(data, list):
        raw_list = data
    else:
        return []
    out: list[dict[str, Any]] = []
    for item in raw_list:
        norm = normalize_intent(item)
        if norm:
            out.append(norm)
    return out


def parse_chat_response(content: str) -> tuple[str, list[dict[str, Any]]]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return content, []
    if not isinstance(data, dict) or "answer" not in data:
        return content, []
    raw = data.get("charts") or []
    if isinstance(raw, dict):
        raw = [raw]
    intents: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:1]:
            norm = normalize_intent(item)
            if norm:
                intents.append(norm)
    answer = str(data.get("answer") or "").strip()
    return answer or content, intents


def analysis_chart_context(analysis: Analysis) -> dict[str, Any]:
    raw = analysis.summary or {}
    return {
        "title": analysis.title,
        "overview": (analysis.overview_text or "")[:2000],
        "n_rows": raw.get("n_rows"),
        "n_cols": raw.get("n_cols"),
        "schema": (raw.get("schema") or [])[:40],
        "numeric_stats": dict(list((raw.get("numeric_stats") or {}).items())[:15]),
        "correlations": dict(list((raw.get("correlations") or {}).items())[:10]),
        "categorical_top": dict(list((raw.get("categorical_top") or {}).items())[:8]),
        "column_labels": raw.get("column_labels") or {},
    }


def plan_chart_intents(llm, analysis: Analysis, *, min_charts: int, max_charts: int) -> list[dict[str, Any]]:
    messages = [
        {
            "role": "system",
            "content": _plan_system(min_charts, max_charts),
        },
        {
            "role": "user",
            "content": json.dumps(analysis_chart_context(analysis), ensure_ascii=False)[:14000],
        },
    ]
    result = llm.complete(
        {"use": "charts", "messages": messages, "response_format": {"type": "json_object"}}
    )
    try:
        intents = parse_intent_list(result["content"])
    except json.JSONDecodeError:
        intents = []
    return intents[:max_charts]
