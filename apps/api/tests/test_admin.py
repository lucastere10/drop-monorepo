import uuid

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from accounts.models import CreditTransaction, Tier, User
from core.models import Analysis, UploadedFile


def _user(email: str, *, staff: bool = False, superuser: bool = False) -> User:
    user = User.objects.create_user(email=email)
    fields = []
    if staff:
        user.is_staff = True
        fields.append("is_staff")
    if superuser:
        user.is_superuser = True
        user.is_staff = True
        fields.extend(["is_superuser", "is_staff"])
    if fields:
        user.save(update_fields=list(dict.fromkeys(fields)))
    return user


def _client(user: User | None = None) -> APIClient:
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _analysis(*, user: User | None, title: str) -> Analysis:
    uploaded = UploadedFile.objects.create(
        user=user,
        original_name="dados.csv",
        size_bytes=12,
        storage_key=f"uploads/{uuid.uuid4()}.csv",
    )
    return Analysis.objects.create(
        user=user,
        uploaded_file=uploaded,
        title=title,
        n_rows=4,
        n_cols=2,
    )


@pytest.fixture
def staff(db):
    return _user("staff@example.com", staff=True)


@pytest.fixture
def regular(db):
    return _user("regular@example.com")


def test_anonymous_and_regular_are_forbidden(db, regular):
    anon = _client().get("/api/admin/overview/")
    assert anon.status_code == 403

    user_client = _client(regular)
    denied = user_client.get("/api/admin/users/")
    assert denied.status_code == 403
    assert denied.json()["code"] == "error"


def test_me_includes_is_staff(db, staff, regular):
    staff_me = _client(staff).get("/api/auth/me/")
    assert staff_me.status_code == 200
    assert staff_me.json()["is_staff"] is True

    regular_me = _client(regular).get("/api/auth/me/")
    assert regular_me.json()["is_staff"] is False


def test_staff_lists_users_and_anonymous_analysis(db, staff):
    _analysis(user=None, title="sem dono")
    client = _client(staff)

    users = client.get("/api/admin/users/")
    assert users.status_code == 200
    emails = {row["email"] for row in users.json()}
    assert "staff@example.com" in emails

    analyses = client.get("/api/admin/analyses/")
    assert analyses.status_code == 200
    rows = analyses.json()
    anon = next(row for row in rows if row["title"] == "sem dono")
    assert anon["is_anonymous"] is True
    assert anon["user_email"] is None
    assert "storage_key" not in anon
    assert "summary" not in anon

    overview = client.get("/api/admin/overview/")
    assert overview.status_code == 200
    body = overview.json()
    assert body["analyses_anonymous"] == 1
    assert body["users_total"] >= 1
    assert "queued" in body["jobs_by_status"]


def test_adjust_credits_writes_ledger(db, staff, regular):
    client = _client(staff)
    before = regular.credit_account.balance
    resp = client.post(
        f"/api/admin/users/{regular.id}/credits/",
        {"delta": 100, "reason": "teste local"},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tx_type"] == CreditTransaction.TxType.ADJUST
    assert body["action"] == "admin.adjust"
    assert body["amount"] == 100
    assert body["balance_after"] == before + 100

    regular.credit_account.refresh_from_db()
    assert regular.credit_account.balance == before + 100
    tx = CreditTransaction.objects.get(pk=body["id"])
    assert tx.meta["admin"] == "staff@example.com"
    assert tx.meta["reason"] == "teste local"


def test_adjust_cannot_go_negative(db, staff, regular):
    account = regular.credit_account
    before = account.balance
    resp = _client(staff).post(
        f"/api/admin/users/{regular.id}/credits/",
        {"delta": -(before + 1), "reason": "zerar demais"},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "insufficient_credits"
    account.refresh_from_db()
    assert account.balance == before
    assert not CreditTransaction.objects.filter(
        user=regular, tx_type=CreditTransaction.TxType.ADJUST
    ).exists()


def test_staff_cannot_promote(db, staff, regular):
    resp = _client(staff).patch(
        f"/api/admin/users/{regular.id}/",
        {"is_staff": True},
        format="json",
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
    regular.refresh_from_db()
    assert regular.is_staff is False


def test_staff_cannot_deactivate_self(db, staff):
    resp = _client(staff).patch(
        f"/api/admin/users/{staff.id}/",
        {"is_active": False},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "cannot_deactivate_self"
    staff.refresh_from_db()
    assert staff.is_active is True


def test_tier_change_does_not_grant_credits(db, staff, regular):
    Tier.objects.create(
        slug="pro",
        name="Pro",
        credits_per_period=2000,
        max_upload_mb=50,
        max_rows=500_000,
        features=["chat"],
    )
    before = regular.credit_account.balance
    resp = _client(staff).patch(
        f"/api/admin/users/{regular.id}/",
        {"tier": "pro"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["tier"] == "pro"
    assert resp.json()["balance"] == before
    regular.credit_account.refresh_from_db()
    assert regular.credit_account.tier.slug == "pro"
    assert regular.credit_account.balance == before


def test_promote_staff_command(db):
    user = User.objects.create_user(email="op@example.com")
    call_command("promote_staff", "OP@example.com")
    user.refresh_from_db()
    assert user.is_staff is True
    assert not user.has_usable_password()

    with pytest.raises(CommandError):
        call_command("promote_staff", "missing@example.com")
