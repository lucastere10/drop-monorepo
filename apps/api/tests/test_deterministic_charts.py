import pandas as pd
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, Tier
from core.models import ChartSpec
from core.services.deterministic_charts import build_deterministic_chart_specs
from core.services.profiling import profile_dataframe


def test_build_categorical_and_histogram_charts():
    df = pd.DataFrame(
        {
            "categoria": ["a", "a", "b", "b", "b", "c"] * 5,
            "valor": [1, 2, 3, 10, 12, 11, 9, 8, 7, 6, 5, 4, 3, 2, 1] * 2,
        }
    )
    summary = profile_dataframe(df, sample_rows=5)
    specs = build_deterministic_chart_specs(df, summary)
    assert len(specs) >= 1
    assert all(s["spec"]["source"] == "deterministic" for s in specs)
    assert all(s["spec"]["labels"] and s["spec"]["values"] for s in specs)
    rules = {s["spec"]["rule"] for s in specs}
    assert "categorical_top_n" in rules or "numeric_histogram" in rules


def test_surrogate_keys_are_not_plotted():
    rng = pd.Series(range(40))
    df = pd.DataFrame(
        {
            "x": rng,
            "y": rng * 2 + 1,
            "z": rng[::-1].reset_index(drop=True),
        }
    )
    summary = profile_dataframe(df, sample_rows=5)
    specs = build_deterministic_chart_specs(df, summary, max_charts=8)
    rules = [spec["spec"]["rule"] for spec in specs]
    columns = [col for spec in specs for col in spec["spec"]["columns"]]
    assert "corr_pair_bar" not in rules
    assert "x" not in columns
    assert "z" not in columns


def test_empty_or_unplottable_returns_no_charts():
    specs = build_deterministic_chart_specs(
        pd.DataFrame(),
        {"schema": [], "categorical_top": {}, "numeric_stats": {}, "correlations": {}},
    )
    assert specs == []


@pytest.fixture
def upload_client(db, monkeypatch):
    Tier.objects.get_or_create(
        slug="free",
        defaults={
            "name": "Free",
            "credits_per_period": 100,
            "max_upload_mb": 10,
            "max_rows": 50_000,
            "features": ["chat", "overview", "insights", "charts"],
            "is_default": True,
        },
    )
    ActionCost.objects.get_or_create(action="analysis.upload", defaults={"cost": 1})
    ActionCost.objects.get_or_create(action="ai.overview", defaults={"cost": 5})
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    user = get_user_model().objects.create_user(email="charts@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_upload_persists_deterministic_charts(upload_client):
    content = b"name,value\na,1\na,2\nb,3\nb,4\nc,5\nc,6\n"
    f = SimpleUploadedFile("sample.csv", content, content_type="text/csv")
    resp = upload_client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    analysis_id = resp.json()["id"]
    charts = ChartSpec.objects.filter(analysis_id=analysis_id)
    assert charts.count() >= 1
    assert all((c.spec or {}).get("source") == "deterministic" for c in charts)
    assert all((c.spec or {}).get("description") for c in charts)
    layout = resp.json()["dashboard_layout"]
    assert len(layout["lg"]) == charts.count()

    listed = upload_client.get(f"/api/analyses/{analysis_id}/charts-list/")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
