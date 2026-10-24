import json
from types import SimpleNamespace

import pandas as pd
import pytest

from core.models import Analysis, ChartSpec, UploadedFile
from core.services.chart_compiler import compile_intent
from core.services.chart_format import format_chart_number
from core.services.chart_planner import _plan_system, analysis_chart_context
from core.services.column_labels import parse_column_labels, replace_column_tokens
from core.services.deterministic_charts import build_deterministic_chart_specs
from core.services.profiling import profile_dataframe
from workers.models import Job
from workers.services.runner import handle_overview


def test_format_avoids_scientific_notation_for_ordinary_numbers():
    assert format_chart_number(100) == "100"
    assert format_chart_number(48.6) == "48,6"
    assert "e" in format_chart_number(0.00001).lower()


def test_histogram_bins_have_no_scientific_notation():
    df = pd.DataFrame(
        {
            "attendance_rate": [40, 50, 60, 70, 80, 90, 100, 45, 55, 65, 75, 85, 95, 42, 99],
        }
    )
    summary = profile_dataframe(df, sample_rows=5)
    specs = build_deterministic_chart_specs(df, summary)
    hist = next(spec for spec in specs if spec["spec"]["rule"] == "numeric_histogram")
    labels = hist["spec"]["labels"]
    assert labels
    assert all("e+" not in label.lower() and "e-" not in label.lower() for label in labels)
    assert any(label.endswith("100") for label in labels)
    assert hist["spec"]["description"] == "quantidade de registros em cada intervalo"
    assert hist["spec"]["value_label"] == "frequência"


def test_identifier_columns_are_not_histograms():
    df = pd.DataFrame(
        {
            "student_id": list(range(1, 31)),
            "codigo": list(range(1, 31)),
            "attendance_rate": [40 + (i % 12) for i in range(30)],
        }
    )
    summary = profile_dataframe(df, sample_rows=5)
    specs = build_deterministic_chart_specs(df, summary)
    histogram_cols = [
        col
        for spec in specs
        if spec["spec"]["rule"] == "numeric_histogram"
        for col in spec["spec"]["columns"]
    ]
    assert "student_id" not in histogram_cols
    assert "codigo" not in histogram_cols
    assert "attendance_rate" in histogram_cols


def test_unique_floats_still_get_a_histogram():
    df = pd.DataFrame({"preco": [10.5 + i * 0.37 for i in range(20)]})
    summary = profile_dataframe(df, sample_rows=5)
    specs = build_deterministic_chart_specs(df, summary)
    cols = [
        col
        for spec in specs
        if spec["spec"]["rule"] == "numeric_histogram"
        for col in spec["spec"]["columns"]
    ]
    assert "preco" in cols


def test_replace_uses_longer_column_name_first():
    text = replace_column_tokens(
        "Distribuição de final_grade",
        {"grade": "Nota", "final_grade": "Notas finais"},
    )
    assert text == "Distribuição de Notas finais"


def test_parse_keeps_only_known_columns():
    raw = json.dumps(
        {"labels": {"parent_education": "Educação dos pais", "inventada": "Fantasma"}}
    )
    labels = parse_column_labels(raw, {"parent_education"})
    assert labels == {"parent_education": "Educação dos pais"}


def test_compile_rewrites_title_and_keeps_bins():
    df = pd.DataFrame({"attendance_rate": list(range(40, 70))})
    payload = compile_intent(
        df,
        {"column_labels": {"attendance_rate": "Frequência de presença"}},
        {
            "title": "Distribuição de attendance_rate",
            "kind": "histogram",
            "columns": ["attendance_rate"],
            "chart_type": "bar",
        },
    )
    assert payload is not None
    assert payload["title"] == "Distribuição de Frequência de presença"
    assert all("e+" not in label.lower() for label in payload["spec"]["labels"])
    assert "attendance_rate" not in "".join(payload["spec"]["labels"])
    assert payload["spec"]["value_label"] == "frequência"
    assert payload["spec"]["columns"] == ["attendance_rate"]


def test_planner_context_exposes_column_labels():
    analysis = SimpleNamespace(
        title="alunos",
        overview_text="",
        summary={"column_labels": {"parent_education": "Educação dos pais"}, "n_rows": 4, "n_cols": 1},
    )
    context = analysis_chart_context(analysis)
    assert context["column_labels"]["parent_education"] == "Educação dos pais"
    assert "column_labels" in _plan_system(1, 3)
    assert "snake_case" in _plan_system(1, 3)


class ScriptedLLM:
    def __init__(self, contents: list[str]):
        self.contents = contents
        self.calls = 0

    def complete(self, request):
        content = self.contents[self.calls]
        self.calls += 1
        return {"content": content, "provider": "fake", "model": "fake"}


def _analysis_with_charts() -> tuple[Analysis, ChartSpec, ChartSpec]:
    uploaded = UploadedFile.objects.create(
        original_name="alunos.csv",
        content_type="text/csv",
        size_bytes=20,
        storage_key="alunos.csv",
    )
    analysis = Analysis.objects.create(
        uploaded_file=uploaded,
        title="alunos",
        n_rows=10,
        n_cols=2,
        summary={
            "n_rows": 10,
            "n_cols": 2,
            "schema": [
                {"name": "parent_education", "dtype": "object", "example": "high school"},
                {"name": "final_grade", "dtype": "float64", "example": "88"},
            ],
        },
    )
    histogram = ChartSpec.objects.create(
        analysis=analysis,
        title="Distribuição de parent_education",
        chart_type="bar",
        spec={
            "title": "Distribuição de parent_education",
            "description": "quantidade de registros em cada intervalo",
            "labels": ["parent_education", "90–100"],
            "values": [4, 6],
            "rule": "numeric_histogram",
            "columns": ["parent_education"],
        },
    )
    correlation = ChartSpec.objects.create(
        analysis=analysis,
        title="Correlações mais fortes",
        chart_type="bar",
        spec={
            "title": "Correlações mais fortes",
            "description": "força da relação entre pares numéricos",
            "labels": ["parent_education×final_grade"],
            "values": [0.4],
            "rule": "corr_pair_bar",
            "columns": ["parent_education", "final_grade"],
        },
    )
    return analysis, histogram, correlation


@pytest.mark.django_db
def test_overview_applies_labels_without_touching_bins(monkeypatch):
    analysis, histogram, correlation = _analysis_with_charts()
    llm = ScriptedLLM(
        [
            "Resumo executivo do arquivo.",
            json.dumps(
                {
                    "labels": {
                        "parent_education": "Educação dos pais",
                        "final_grade": "Notas finais",
                        "inventada": "Fantasma",
                    }
                }
            ),
        ]
    )
    monkeypatch.setattr("workers.services.runner.get_llm_client", lambda: llm)
    job = Job.objects.create(
        job_type="ai_overview",
        analysis=analysis,
        payload={"analysis_id": str(analysis.id)},
    )
    result = handle_overview(job)
    analysis.refresh_from_db()
    histogram.refresh_from_db()
    correlation.refresh_from_db()

    assert result["overview"] == "Resumo executivo do arquivo."
    assert analysis.overview_text == "Resumo executivo do arquivo."
    assert analysis.summary["column_labels"] == {
        "parent_education": "Educação dos pais",
        "final_grade": "Notas finais",
    }
    assert histogram.title == "Distribuição de Educação dos pais"
    assert histogram.spec["labels"] == ["parent_education", "90–100"]
    assert correlation.spec["labels"] == ["Educação dos pais×Notas finais"]


@pytest.mark.django_db
def test_overview_survives_invalid_label_json(monkeypatch):
    analysis, histogram, _correlation = _analysis_with_charts()
    llm = ScriptedLLM(["Resumo que permanece.", "nao-e-json"])
    monkeypatch.setattr("workers.services.runner.get_llm_client", lambda: llm)
    job = Job.objects.create(
        job_type="ai_overview",
        analysis=analysis,
        payload={"analysis_id": str(analysis.id)},
    )
    result = handle_overview(job)
    analysis.refresh_from_db()
    histogram.refresh_from_db()

    assert result["overview"] == "Resumo que permanece."
    assert analysis.overview_text == "Resumo que permanece."
    assert "column_labels" not in (analysis.summary or {})
    assert histogram.title == "Distribuição de parent_education"
