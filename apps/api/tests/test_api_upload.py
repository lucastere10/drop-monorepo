import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, Tier


@pytest.fixture
def api_client(db, monkeypatch):
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
    user = get_user_model().objects.create_user(email="api@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def test_health(db):
    client = APIClient()
    resp = client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_overview_insufficient_credits(api_client):
    client, user = api_client
    user.credit_account.balance = 1
    user.credit_account.save(update_fields=["balance"])
    content = b"name,value\na,1\nb,2\n"
    uploaded = SimpleUploadedFile("sample.csv", content, content_type="text/csv")
    resp = client.post("/api/analyses/", {"file": uploaded}, format="multipart")
    assert resp.status_code == 402
    body = resp.json()
    assert body["code"] == "insufficient_credits"
    assert "créditos suficientes" in body["message"]
    assert body["details"] == {"required": 5, "balance": 1}
    user.credit_account.refresh_from_db()
    assert user.credit_account.balance == 1


def test_upload_analysis(api_client):
    client, _user = api_client
    content = b"name,value\na,1\nb,2\nc,3\n"
    f = SimpleUploadedFile("sample.csv", content, content_type="text/csv")
    resp = client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    assert data["n_rows"] == 3
    assert "summary" in data
    assert data["quality_grade"]
    assert data["overview_job_id"]
