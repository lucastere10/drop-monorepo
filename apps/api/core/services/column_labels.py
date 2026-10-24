from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_LABELS_SYSTEM = (
    "Você nomeia colunas de uma planilha para um gestor brasileiro. "
    'Responda APENAS JSON válido: {"labels": {"nome_original": "Rótulo curto"}}. '
    "Uma entrada para cada coluna recebida; a chave é exatamente o nome original. "
    "Português do Brasil, curto (2 a 4 palavras), sem snake_case. "
    "Se o nome já for claro em português, só ajuste a capitalização. "
    "Não invente colunas. Não traduza valores, só o nome."
)

_CORR_RULES = {"corr_pair_bar", "correlation"}


def parse_column_labels(content: str, allowed: set[str]) -> dict[str, str]:
    data = json.loads(content)
    raw = data.get("labels") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    labels: dict[str, str] = {}
    for key, value in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        label = str(value).strip()[:80]
        if label and label != name:
            labels[name] = label
    return labels


def fetch_column_labels(llm, schema: list[dict[str, Any]]) -> dict[str, str]:
    allowed = {str(col["name"]) for col in schema if col.get("name")}
    if not allowed:
        return {}
    columns = [
        {
            "name": col.get("name"),
            "dtype": col.get("dtype"),
            "example": col.get("example"),
        }
        for col in schema
        if col.get("name")
    ][:40]
    try:
        result = llm.complete(
            {
                "use": "overview",
                "messages": [
                    {"role": "system", "content": _LABELS_SYSTEM},
                    {
                        "role": "user",
                        "content": json.dumps({"columns": columns}, ensure_ascii=False),
                    },
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 1024,
            }
        )
        return parse_column_labels(result["content"], allowed)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.warning("column label response was not usable")
        return {}


def replace_column_tokens(text: str, labels: dict[str, Any]) -> str:
    usable = {
        str(name): str(label)
        for name, label in labels.items()
        if name and label and str(name) != str(label)
    }
    if not text or not usable:
        return text
    ordered = sorted(usable, key=len, reverse=True)
    pattern = re.compile("|".join(rf"(?<![\w]){re.escape(name)}(?![\w])" for name in ordered))
    return pattern.sub(lambda match: usable[match.group(0)], text)


def present_chart_text(
    summary: dict[str, Any],
    *,
    title: str,
    description: str,
    kind: str,
    labels: list[str],
) -> tuple[str, str, list[str]]:
    mapping = summary.get("column_labels")
    if not isinstance(mapping, dict) or not mapping:
        return title[:200], description[:300], labels
    title = replace_column_tokens(title, mapping)[:200]
    description = replace_column_tokens(description, mapping)[:300]
    if kind == "correlation":
        labels = [replace_column_tokens(str(item), mapping)[:40] for item in labels]
    return title, description, labels


def assign_column_labels(llm, analysis) -> dict[str, str]:
    """Persist display names and rewrite existing chart titles. Numbers stay put."""
    from core.models import ChartSpec

    schema = [col for col in ((analysis.summary or {}).get("schema") or []) if col.get("name")]
    labels = fetch_column_labels(llm, schema)
    if not labels:
        return {}
    summary = dict(analysis.summary or {})
    summary["column_labels"] = labels
    analysis.summary = summary
    analysis.save(update_fields=["summary", "updated_at"])
    _rewrite_charts(ChartSpec.objects.filter(analysis=analysis), labels)
    return labels


def _rewrite_charts(charts, labels: dict[str, str]) -> None:
    for chart in charts:
        spec = dict(chart.spec or {})
        title = replace_column_tokens(chart.title or "", labels)[:200]
        spec_title = replace_column_tokens(str(spec.get("title") or ""), labels)[:200]
        description = replace_column_tokens(str(spec.get("description") or ""), labels)[:300]
        axis = list(spec.get("labels") or [])
        if spec.get("rule") in _CORR_RULES:
            axis = [replace_column_tokens(str(item), labels)[:40] for item in axis]
        unchanged = (
            title == (chart.title or "")
            and spec_title == str(spec.get("title") or "")
            and description == str(spec.get("description") or "")
            and axis == list(spec.get("labels") or [])
        )
        if unchanged:
            continue
        spec["title"] = spec_title or title
        spec["description"] = description
        if spec.get("rule") in _CORR_RULES:
            spec["labels"] = axis
        chart.title = title
        chart.spec = spec
        chart.save(update_fields=["title", "spec"])
