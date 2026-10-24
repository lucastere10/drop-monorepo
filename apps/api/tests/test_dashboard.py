import json
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, Tier
from core.models import ChartSpec
from workers.models import Job


class _DashLLM:
    def complete(self, req):
        body = {
            "charts": [
                {
                    "title": "Pedidos por região",
                    "description": "contagem das regiões",
                    "chart_type": "bar",
                    "kind": "groupby",
                    "columns": ["regiao"],
                    "agg": "count",
                    "labels": ["inventado"],
                    "values": [999],
                },
                {
                    "title": "Faixas de valor",
                    "description": "histograma",
                    "chart_type": "bar",
                    "kind": "histogram",
                    "columns": ["valor"],
                    "agg": "count",
                },
            ]
        }
        return {
            "content": json.dumps(body),
            "provider": "fake",
            "model": "fake",
            "input_tokens": 1,
            "output_tokens": 1,
        }


@pytest.fixture
def dash_client(db, monkeypatch):
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
    for action, cost in [
        ("analysis.upload", 1),
        ("ai.overview", 5),
        ("ai.dashboard", 15),
    ]:
        ActionCost.objects.get_or_create(action=action, defaults={"cost": cost})
    monkeypatch.setattr("workers.services.runner.get_llm_client", lambda: _DashLLM())
    user = get_user_model().objects.create_user(email="dash@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _upload(client, csv: bytes):
    f = SimpleUploadedFile("s.csv", csv, content_type="text/csv")
    resp = client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()["id"]


CSV = (
    b"regiao,valor\n"
    b"sul,1\nsul,2\nnorte,3\nnorte,4\nnorte,8\nleste,5\n"
)


@pytest.mark.django_db(transaction=True)
def test_dashboard_endpoint_is_gone(dash_client):
    analysis_id = _upload(dash_client, CSV)
    before = set(ChartSpec.objects.filter(analysis_id=analysis_id).values_list("id", flat=True))
    resp = dash_client.post(f"/api/analyses/{analysis_id}/dashboard/", {}, format="json")
    assert resp.status_code == 410
    assert Job.objects.filter(job_type="ai_dashboard").count() == 0
    created = ChartSpec.objects.filter(analysis_id=analysis_id).exclude(id__in=before)
    assert created.count() == 0


@pytest.mark.django_db
def test_patch_layout_rejects_foreign_chart_and_anonymous(dash_client):
    analysis_id = _upload(dash_client, CSV)
    other_id = _upload(dash_client, b"regiao,valor\na,1\nb,2\n")
    own = ChartSpec.objects.filter(analysis_id=analysis_id).first()
    foreign = ChartSpec.objects.filter(analysis_id=other_id).first()
    assert own and foreign

    ok = dash_client.patch(
        f"/api/analyses/{analysis_id}/",
        {
            "dashboard_layout": {
                "lg": [{"i": str(own.id), "x": 0, "y": 0, "w": 6, "h": 8}],
                "md": [],
                "sm": [],
            }
        },
        format="json",
    )
    assert ok.status_code == 200
    assert ok.json()["dashboard_layout"]["lg"][0]["i"] == str(own.id)

    bad = dash_client.patch(
        f"/api/analyses/{analysis_id}/",
        {
            "dashboard_layout": {
                "lg": [{"i": str(foreign.id), "x": 0, "y": 0, "w": 6, "h": 8}],
                "md": [],
                "sm": [],
            }
        },
        format="json",
    )
    assert bad.status_code == 400

    anon = APIClient()
    denied = anon.patch(
        f"/api/analyses/{analysis_id}/",
        {"dashboard_layout": {"lg": [], "md": [], "sm": []}},
        format="json",
    )
    assert denied.status_code == 401

    missing = dash_client.patch(
        f"/api/analyses/{analysis_id}/",
        {
            "dashboard_layout": {
                "lg": [{"i": str(uuid.uuid4()), "x": 0, "y": 0, "w": 6, "h": 8}],
                "md": [],
                "sm": [],
            }
        },
        format="json",
    )
    assert missing.status_code == 400
