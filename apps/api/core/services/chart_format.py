from __future__ import annotations

import math

HISTOGRAM_DESCRIPTION = "quantidade de registros em cada intervalo"


def format_chart_number(value: float) -> str:
    """Fixed-point label. Scientific notation only for extreme magnitudes."""
    number = float(value)
    if not math.isfinite(number):
        return str(value)
    magnitude = abs(number)
    if magnitude >= 1_000_000 or (magnitude != 0 and magnitude < 1e-4):
        return f"{number:.4g}".replace(".", ",")
    if _is_whole(number):
        return str(round(number))
    decimals = 1 if magnitude >= 10 else 2
    text = f"{number:.{decimals}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def format_bin_label(low: float, high: float) -> str:
    return f"{format_chart_number(low)}–{format_chart_number(high)}"


def _is_whole(number: float) -> bool:
    return abs(number - round(number)) <= 1e-6 * max(1.0, abs(number))
