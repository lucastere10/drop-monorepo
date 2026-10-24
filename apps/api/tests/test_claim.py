import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
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
    ActionCost.objects.get_or_create(action="ai.insights", defaults={"cost": 10})


@pytest.fixture
def user(db, setup_tier):
    return User.objects.create_user(email="claimer@example.com", first_name="Ana")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_claim_anonymous_analysis(auth_client, user, monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    anon = APIClient()
    f = SimpleUploadedFile("sample.csv", b"name,value\na,1\nb,2\n", content_type="text/csv")
    resp = anon.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    analysis_id = resp.json()["id"]
    assert resp.json()["is_anonymous"] is True

    claim = auth_client.post(f"/api/analyses/{analysis_id}/claim/")
    assert claim.status_code == 200
    data = claim.json()
    assert data["is_anonymous"] is False
    assert data["expires_at"] is None

    analysis = Analysis.objects.get(pk=analysis_id)
    assert analysis.user_id == user.id


def test_insights_auto_claims_anonymous(auth_client, monkeypatch):
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: (_ for _ in ()).throw(RuntimeError("skip llm")),
    )
    anon = APIClient()
    f = SimpleUploadedFile("sample.csv", b"name,value\na,1\nb,2\n", content_type="text/csv")
    resp = anon.post("/api/analyses/", {"file": f}, format="multipart")
    analysis_id = resp.json()["id"]

    insights = auth_client.post(f"/api/analyses/{analysis_id}/insights/", {}, format="json")
    # Job may fail (LLM), but ownership/claim must succeed → 202 not 401
    assert insights.status_code == 202
    analysis = Analysis.objects.get(pk=analysis_id)
    assert analysis.user_id is not None
