from __future__ import annotations

from typing import Any

from rest_framework.exceptions import ValidationError

from core.models import Analysis, ChartSpec

MAX_ITEMS = 20
BREAKPOINTS = ("lg", "md", "sm")


def chart_span(chart_type: str, *, cols: int, force_full: bool = False) -> tuple[int, int]:
    if force_full or chart_type == "line":
        return cols, 8
    return max(cols // 2, 1), 8


def _pack(
    charts: list[tuple[str, str]],
    cols: int,
    *,
    force_full: bool = False,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    x = 0
    y = 0
    row_h = 0
    for chart_id, chart_type in charts:
        w, h = chart_span(chart_type, cols=cols, force_full=force_full)
        if x + w > cols:
            x = 0
            y += row_h or h
            row_h = 0
        items.append({"i": chart_id, "x": x, "y": y, "w": w, "h": h})
        x += w
        row_h = max(row_h, h)
        if x >= cols:
            x = 0
            y += row_h
            row_h = 0
    return items


def build_dashboard_layout(charts: list[tuple[str, str]]) -> dict[str, list[dict[str, Any]]]:
    """charts: (chart_id, chart_type)."""
    return {
        "lg": _pack(charts, 12),
        "md": _pack(charts, 12),
        "sm": _pack(charts, 12, force_full=True),
    }


def append_chart_to_layout(
    layout: dict[str, Any] | None,
    *,
    chart_id: str,
    chart_type: str,
) -> dict[str, list[dict[str, Any]]]:
    base = layout if isinstance(layout, dict) else {}
    out: dict[str, list[dict[str, Any]]] = {}
    for bp, force_full in (("lg", False), ("md", False), ("sm", True)):
        items = [dict(it) for it in (base.get(bp) or []) if isinstance(it, dict)]
        items = [it for it in items if str(it.get("i")) != chart_id]
        bottom = 0
        for it in items:
            bottom = max(bottom, int(it.get("y") or 0) + int(it.get("h") or 8))
        w, h = chart_span(chart_type, cols=12, force_full=force_full)
        items.append({"i": chart_id, "x": 0, "y": bottom, "w": w, "h": h})
        out[bp] = items
    return out


def validate_dashboard_layout(layout: Any, analysis: Analysis) -> dict[str, list[dict[str, int | str]]]:
    if layout in (None, {}):
        return {}
    if not isinstance(layout, dict):
        raise ValidationError("Layout deve ser um objeto.")

    allowed = {
        str(cid)
        for cid in ChartSpec.objects.filter(analysis=analysis).values_list("id", flat=True)
    }
    cleaned: dict[str, list[dict[str, int | str]]] = {}
    for bp in BREAKPOINTS:
        raw_items = layout.get(bp, [])
        if raw_items is None:
            raw_items = []
        if not isinstance(raw_items, list):
            raise ValidationError(f"{bp}: lista de itens inválida.")
        if len(raw_items) > MAX_ITEMS:
            raise ValidationError(f"{bp}: no máximo {MAX_ITEMS} gráficos.")
        items: list[dict[str, int | str]] = []
        seen: set[str] = set()
        for raw in raw_items:
            if not isinstance(raw, dict):
                raise ValidationError(f"{bp}: item de layout inválido.")
            chart_id = str(raw.get("i") or "")
            if chart_id not in allowed:
                raise ValidationError(f"Gráfico {chart_id} não pertence à análise.")
            if chart_id in seen:
                raise ValidationError(f"Gráfico {chart_id} repetido.")
            seen.add(chart_id)
            try:
                x = int(raw["x"])
                y = int(raw["y"])
                w = int(raw["w"])
                h = int(raw["h"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValidationError("x, y, w e h são obrigatórios.") from exc
            if not (0 <= x <= 11 and y >= 0 and 1 <= w <= 12 and 2 <= h <= 20):
                raise ValidationError("Posição ou tamanho fora do limite.")
            items.append({"i": chart_id, "x": x, "y": y, "w": w, "h": h})
        cleaned[bp] = items
    return cleaned
