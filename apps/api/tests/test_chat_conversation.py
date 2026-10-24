import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from accounts.models import ActionCost, Tier
from core.models import Conversation, Message
from core.services.conversations import get_or_create_default_conversation, resolve_conversation
from workers.models import Job
from workers.services.runner import run_job


class _FakeLLM:
    def complete(self, req):
        return {
            "content": "resposta teste",
            "provider": "fake",
            "model": "fake",
            "input_tokens": 1,
            "output_tokens": 1,
        }


@pytest.fixture
def chat_client(db, monkeypatch):
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
    monkeypatch.setattr(
        "workers.services.runner.get_llm_client",
        lambda: _FakeLLM(),
    )
    # Skip real overview LLM on upload path if it runs
    monkeypatch.setattr(
        "workers.services.dispatch.get_llm_client",
        lambda: _FakeLLM(),
        raising=False,
    )
    user = get_user_model().objects.create_user(email="chat@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def _upload(client):
    f = SimpleUploadedFile("s.csv", b"name,value\na,1\nb,2\n", content_type="text/csv")
    resp = client.post("/api/analyses/", {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()["id"]


def _run_if_queued(job_id: str):
    job = Job.objects.get(pk=job_id)
    if job.status == Job.Status.QUEUED:
        run_job(job_id)
        job.refresh_from_db()
    return job


@pytest.mark.django_db(transaction=True)
def test_two_chats_share_one_conversation(chat_client):
    client, _user = chat_client
    analysis_id = _upload(client)

    for msg in ("primeira?", "segunda?"):
        resp = client.post(
            f"/api/analyses/{analysis_id}/chat/",
            {"message": msg},
            format="json",
        )
        assert resp.status_code == 202
        job = _run_if_queued(resp.json()["job_id"])
        assert job.status == Job.Status.SUCCEEDED

    assert Conversation.objects.filter(analysis_id=analysis_id).count() == 1
    conv = Conversation.objects.get(analysis_id=analysis_id)
    assert Message.objects.filter(conversation=conv).count() == 4  # 2 user + 2 assistant

    listed = client.get(f"/api/analyses/{analysis_id}/conversations/")
    assert listed.status_code == 200
    data = listed.json()
    assert len(data) == 1
    assert len(data[0]["messages"]) == 4


@pytest.mark.django_db(transaction=True)
def test_invalid_conversation_id_falls_back_to_default(chat_client):
    client, _user = chat_client
    analysis_id = _upload(client)

    resp = client.post(
        f"/api/analyses/{analysis_id}/chat/",
        {"message": "oi", "conversation_id": str(uuid.uuid4())},
        format="json",
    )
    assert resp.status_code == 202
    job = _run_if_queued(resp.json()["job_id"])
    assert job.status == Job.Status.SUCCEEDED
    assert Conversation.objects.filter(analysis_id=analysis_id).count() == 1
    assert job.result["conversation_id"]


@pytest.mark.django_db
def test_resolve_conversation_helpers(db):
    from core.models import Analysis, UploadedFile

    user = get_user_model().objects.create_user(email="c2@example.com")
    uf = UploadedFile.objects.create(
        user=user,
        original_name="t.csv",
        content_type="text/csv",
        size_bytes=10,
        storage_key="test/t.csv",
    )
    analysis = Analysis.objects.create(
        user=user,
        uploaded_file=uf,
        title="t",
        summary={},
        n_rows=1,
        n_cols=1,
    )
    a = get_or_create_default_conversation(analysis)
    b = get_or_create_default_conversation(analysis)
    assert a.id == b.id
    bad = resolve_conversation(analysis, str(uuid.uuid4()))
    assert bad.id == a.id
    good = resolve_conversation(analysis, str(a.id))
    assert good.id == a.id
