from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import ActionCost, Tier, User
from core.models import Analysis


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


@pytest.fixture
def user(db, setup_tier):
    return User.objects.create_user(email="owner@example.com", first_name="Lia")


@pytest.fixture
def auth_client(user, monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def _upload(client, name="sample.csv"):
    f = SimpleUploadedFile(name, b"name,value\na,1\nb,2\nc,3\n", content_type="text/csv")
    resp = client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


def test_owner_publish_and_unpublish(auth_client):
    data = _upload(auth_client)
    analysis_id = data["id"]

    published = auth_client.patch(
        f"/api/analyses/{analysis_id}/",
        {"is_public": True},
        format="json",
    )
    assert published.status_code == 200
    body = published.json()
    assert body["is_public"] is True
    token = body["share_token"]
    assert token

    shared = APIClient().get(f"/api/share/{token}/")
    assert shared.status_code == 200
    assert shared.json()["title"] == data["title"]

    unpublished = auth_client.patch(
        f"/api/analyses/{analysis_id}/",
        {"is_public": False},
        format="json",
    )
    assert unpublished.status_code == 200
    assert unpublished.json()["is_public"] is False

    gone = APIClient().get(f"/api/share/{token}/")
    assert gone.status_code == 404


def test_unknown_share_token_is_404(db):
    resp = APIClient().get("/api/share/not-a-real-token/")
    assert resp.status_code == 404


def test_anonymous_cannot_patch_is_public(setup_tier, monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    anon = APIClient()
    data = _upload(anon)
    resp = anon.patch(
        f"/api/analyses/{data['id']}/",
        {"is_public": True},
        format="json",
    )
    assert resp.status_code == 401


def test_expired_public_share_is_404(setup_tier, monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    anon = APIClient()
    data = _upload(anon)
    analysis = Analysis.objects.get(pk=data["id"])
    analysis.is_public = True
    analysis.ensure_share_token()
    analysis.expires_at = timezone.now() - timedelta(hours=1)
    analysis.save(update_fields=["is_public", "share_token", "expires_at", "updated_at"])

    resp = APIClient().get(f"/api/share/{analysis.share_token}/")
    assert resp.status_code == 404
