import pandas as pd

from core.services.cleaning import clean_dataframe
from core.services.profiling import profile_dataframe


def test_clean_and_profile():
    df = pd.DataFrame(
        {
            " A ": [1, 2, 3, None],
            "b": [" x ", "y", "x", "z"],
            "empty": [None, None, None, None],
            "pct": ["10%", "20%", "30%", "40%"],
        }
    )
    cleaned, report = clean_dataframe(df)
    assert "empty" not in cleaned.columns
    assert "empty" in report["columns_dropped"]
    assert list(cleaned.columns)[:2] == ["A", "b"]
    summary = profile_dataframe(cleaned, sample_rows=2, cleaning=report)
    assert summary["n_rows"] == 4
    assert "quality" in summary
    assert summary["quality_grade"] in {"S", "A", "B", "C", "D", "F"}
    assert "outliers" in summary
    assert len(summary["sample_rows"]) <= 2
