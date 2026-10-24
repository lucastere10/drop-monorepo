import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, Tier


@pytest.fixture
def anon_client(db):
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
    return APIClient()


def test_anonymous_upload(anon_client, monkeypatch):
    # Avoid real LLM during auto overview
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    f = SimpleUploadedFile("sample.csv", b"name,value\na,1\nb,2\nc,3\n", content_type="text/csv")
    resp = anon_client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_anonymous"] is True
    assert data["expires_at"]
    assert data["quality_grade"]
    assert "quality" in data["summary"]
    assert "outliers" in data["summary"]
    analysis_id = data["id"]

    get_resp = anon_client.get(f"/api/analyses/{analysis_id}/")
    assert get_resp.status_code == 200

    # Soft wall on chat
    chat = anon_client.post(
        f"/api/analyses/{analysis_id}/chat/",
        {"message": "oi"},
        format="json",
    )
    assert chat.status_code == 401
