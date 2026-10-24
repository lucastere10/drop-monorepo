from __future__ import annotations

from typing import Any

from core.models import Analysis


class AnalysisTools:
    def __init__(self, analysis: Analysis):
        self.analysis = analysis
        self.summary: dict[str, Any] = analysis.summary or {}

    def schema(self) -> list[dict[str, Any]]:
        return list(self.summary.get("schema") or [])

    def stats(self) -> dict[str, Any]:
        return {
            "n_rows": self.summary.get("n_rows"),
            "n_cols": self.summary.get("n_cols"),
            "numeric_stats": self.summary.get("numeric_stats") or {},
            "quality_score": self.summary.get("quality_score"),
            "duplicates": self.summary.get("duplicates"),
        }

    def sample(self, n: int = 5) -> list[dict[str, Any]]:
        rows = self.summary.get("sample_rows") or []
        return rows[:n]

    def aggregate(self, column: str, fn: str = "sum") -> Any:
        stats = (self.summary.get("numeric_stats") or {}).get(column)
        if not stats:
            return None
        if fn == "sum":
            # approximate from mean * rows if present
            mean = stats.get("mean")
            n = self.summary.get("n_rows") or 0
            if mean is None:
                return None
            return mean * n
        return stats.get(fn)
