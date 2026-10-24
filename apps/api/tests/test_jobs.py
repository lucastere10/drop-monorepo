import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, CreditTransaction, Tier
from accounts.services.credits import refund
from workers.models import Job
from workers.services.runner import run_job


@pytest.fixture
def seeded(db):
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
        ("ai.chat_message", 3),
    ]:
        ActionCost.objects.get_or_create(action=action, defaults={"cost": cost})
    user = get_user_model().objects.create_user(email="jobs@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db(transaction=True)
def test_job_failure_refunds_once(seeded, monkeypatch):
    client, user = seeded
    f = SimpleUploadedFile("s.csv", b"a,b\n1,2\n", content_type="text/csv")
    up = client.post("/api/analyses/", {"file": f}, format="multipart")
    assert up.status_code == 201
    analysis_id = up.json()["id"]

    def boom(*_a, **_k):
        raise RuntimeError("llm down")

    monkeypatch.setattr("workers.services.runner.get_llm_client", boom)
    resp = client.post(f"/api/analyses/{analysis_id}/overview/", {}, format="json")
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job = Job.objects.get(pk=job_id)
    if job.status == Job.Status.QUEUED:
        run_job(job_id)
        job.refresh_from_db()

    assert job.status == Job.Status.FAILED
    assert job.credits_refunded is True
    refunds = CreditTransaction.objects.filter(
        reference_id=job_id, tx_type=CreditTransaction.TxType.REFUND
    )
    assert refunds.count() == 1

    # idempotent refund
    refund(user, action="ai.overview", reference_id=job_id)
    assert (
        CreditTransaction.objects.filter(
            reference_id=job_id, tx_type=CreditTransaction.TxType.REFUND
        ).count()
        == 1
    )
