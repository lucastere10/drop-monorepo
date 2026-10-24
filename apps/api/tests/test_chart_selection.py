import pandas as pd

from core.services.chart_compiler import compile_intent
from core.services.deterministic_charts import build_deterministic_chart_specs
from core.services.profiling import profile_dataframe


def _rules(specs: list[dict]) -> list[str]:
    return [spec["spec"]["rule"] for spec in specs]


def _columns(specs: list[dict], rule: str) -> list[str]:
    found: list[str] = []
    for spec in specs:
        if spec["spec"]["rule"] == rule:
            found.extend(spec["spec"]["columns"])
    return found


def test_rankings_stop_at_two_and_total_stays_within_cap():
    frame = {
        f"cat_{i}": (["a", "b", "c", "d"] * 8)[:30]
        for i in range(4)
    }
    frame["nota"] = [i % 7 for i in range(30)]
    df = pd.DataFrame(frame)
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    assert len(specs) <= 8
    assert _rules(specs).count("categorical_top_n") == 2
    assert "corr_pair_bar" not in _rules(specs)


def test_identifier_and_surrogate_skip_histogram():
    df = pd.DataFrame(
        {
            "student_id": list(range(1, 31)),
            "codigo": list(range(1, 31)),
            "attendance_rate": [40 + (i % 12) for i in range(30)],
        }
    )
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    columns = _columns(specs, "numeric_histogram")
    assert "student_id" not in columns
    assert "codigo" not in columns
    assert "attendance_rate" in columns


def test_relative_spread_prefers_rate_over_large_scale():
    large = [10000 + i * 100 for i in range(30)]
    third = [5000 + i * 40 for i in range(30)]
    rate = [i * 2 for i in range(30)]
    df = pd.DataFrame({"receita": large, "meio": third, "taxa": rate})
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    columns = _columns(specs, "numeric_histogram")
    assert columns[0] == "taxa"
    assert "meio" not in columns
    assert len(columns) == 2


def test_no_line_without_a_date_and_no_missingness_without_nulls():
    df = pd.DataFrame({"nota": [i % 5 for i in range(20)]})
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    assert "datetime_line" not in _rules(specs)
    assert "missingness" not in _rules(specs)


def test_missingness_lists_incomplete_columns():
    df = pd.DataFrame(
        {
            "cidade": ["a", None, "a", "b", None, "b", "a", "b", "a", "b"],
            "nota": list(range(10)),
        }
    )
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    missing = next(spec for spec in specs if spec["spec"]["rule"] == "missingness")
    assert missing["spec"]["orientation"] == "horizontal"
    assert missing["spec"]["value_label"] == "ausência (%)"
    assert "cidade" in missing["spec"]["labels"]
    assert "nota" not in missing["spec"]["labels"]


def test_pie_only_for_two_or_three_balanced_parts():
    balanced = pd.DataFrame({"lado": ["a", "b"] * 10})
    many = pd.DataFrame({"grau": ["fundamental", "médio", "superior", "pós"] * 6})
    dominated = pd.DataFrame({"status": ["ok"] * 18 + ["falha", "pendente"]})
    balanced_specs = build_deterministic_chart_specs(balanced, profile_dataframe(balanced))
    many_specs = build_deterministic_chart_specs(many, profile_dataframe(many))
    dominated_specs = build_deterministic_chart_specs(dominated, profile_dataframe(dominated))
    assert balanced_specs[0]["chart_type"] == "pie"
    assert many_specs[0]["chart_type"] == "bar"
    assert many_specs[0]["spec"]["orientation"] == "horizontal"
    assert dominated_specs[0]["chart_type"] == "bar"
    assert dominated_specs[0]["spec"]["orientation"] == "horizontal"


def test_line_when_a_date_column_exists():
    df = pd.DataFrame(
        {
            "dia": pd.date_range("2024-01-01", periods=12, freq="D"),
            "valor": [1, 4, 2, 8, 3, 9, 2, 5, 7, 1, 6, 4],
        }
    )
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    assert "datetime_line" in _rules(specs)
    assert "corr_pair_bar" not in _rules(specs)


def test_histogram_bins_avoid_scientific_notation():
    df = pd.DataFrame(
        {"attendance_rate": [40, 50, 60, 70, 80, 90, 100, 45, 55, 65, 75, 85, 95, 42, 99]}
    )
    specs = build_deterministic_chart_specs(df, profile_dataframe(df, sample_rows=5))
    hist = next(spec for spec in specs if spec["spec"]["rule"] == "numeric_histogram")
    assert all("e+" not in label.lower() for label in hist["spec"]["labels"])


def test_compiler_rejects_correlation_and_identifier():
    df = pd.DataFrame(
        {
            "student_id": list(range(1, 21)),
            "regiao": ["sul", "norte"] * 10,
        }
    )
    summary = profile_dataframe(df, sample_rows=5)
    assert (
        compile_intent(
            df,
            summary,
            {"kind": "correlation", "columns": ["student_id", "regiao"], "chart_type": "bar"},
        )
        is None
    )
    assert (
        compile_intent(
            df,
            summary,
            {"kind": "histogram", "columns": ["student_id"], "chart_type": "bar"},
        )
        is None
    )
