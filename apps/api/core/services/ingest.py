from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        for enc in ("utf-8", "latin-1"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"Formato não suportado: {suffix}")
