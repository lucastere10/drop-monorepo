from datetime import timedelta
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import ActionCost, Tier, User
from core.models import Analysis
from core.services.cleanup import cleanup_expired_uploads
from core.services.storage import get_storage


@pytest.fixture
def setup_tier(db):
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
    ActionCost.objects.get_or_create(action="ai.insights", defaults={"cost": 10})


@pytest.fixture
def skip_llm(monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )


def _csv(name="sample.csv"):
    return SimpleUploadedFile(name, b"name,value\na,1\nb,2\nc,3\n", content_type="text/csv")


def _auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@override_settings(RATE_LIMIT_ANON_UPLOAD_PER_HOUR=2)
def test_anon_upload_rate_limit(setup_tier, skip_llm):
    client = APIClient()
    first = client.post("/api/analyses/", {"file": _csv("a.csv")}, format="multipart")
    assert first.status_code == 201
    assert first.json()["overview_job_id"]

    second = client.post("/api/analyses/", {"file": _csv("b.csv")}, format="multipart")
    assert second.status_code == 201

    third = client.post("/api/analyses/", {"file": _csv("c.csv")}, format="multipart")
    assert third.status_code == 429
    assert third.json()["code"] == "rate_limited"


@override_settings(RATE_LIMIT_AUTH_UPLOAD_PER_HOUR=1)
def test_auth_upload_rate_limit(setup_tier, skip_llm):
    user = User.objects.create_user(email="limiter@example.com")
    client = _auth_client(user)
    first = client.post("/api/analyses/", {"file": _csv()}, format="multipart")
    assert first.status_code == 201

    second = client.post("/api/analyses/", {"file": _csv("two.csv")}, format="multipart")
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"


@override_settings(RATE_LIMIT_AI_JOBS_PER_HOUR=1)
def test_ai_jobs_rate_limit(setup_tier, skip_llm):
    user = User.objects.create_user(email="ai@example.com")
    auth = _auth_client(user)
    anon = APIClient()
    uploaded = anon.post("/api/analyses/", {"file": _csv()}, format="multipart")
    assert uploaded.status_code == 201
    analysis_id = uploaded.json()["id"]

    first = auth.post(f"/api/analyses/{analysis_id}/insights/", {}, format="json")
    assert first.status_code == 202

    second = auth.post(f"/api/analyses/{analysis_id}/insights/", {}, format="json")
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"


def test_cleanup_expired_anonymous_analysis(setup_tier, skip_llm, tmp_path, settings):
    settings.LOCAL_STORAGE_ROOT = str(tmp_path)
    client = APIClient()
    resp = client.post("/api/analyses/", {"file": _csv()}, format="multipart")
    assert resp.status_code == 201
    analysis = Analysis.objects.get(pk=resp.json()["id"])
    key = analysis.uploaded_file.storage_key
    analysis.expires_at = timezone.now() - timedelta(hours=1)
    analysis.save(update_fields=["expires_at", "updated_at"])

    assert Path(get_storage().open(key)).exists()
    deleted = cleanup_expired_uploads(days=30)
    assert deleted >= 1
    assert not Analysis.objects.filter(pk=analysis.pk).exists()
    with pytest.raises(FileNotFoundError):
        get_storage().open(key)


def test_cron_cleanup_requires_internal_token(db):
    client = APIClient()
    denied = client.post("/internal/workers/cron_cleanup_uploads/", {}, format="json")
    assert denied.status_code == 403


def test_cron_cleanup_endpoint_ok(setup_tier, skip_llm, settings):
    client = APIClient()
    client.credentials(HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_WORKER_TOKEN)
    resp = client.post("/internal/workers/cron_cleanup_uploads/", {}, format="json")
    assert resp.status_code == 200
    assert resp.json()["status"] in {"succeeded", "failed"}
