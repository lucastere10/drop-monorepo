import pytest
from django.contrib.auth import get_user_model

from accounts.models import ActionCost, Tier
from accounts.services.credits import InsufficientCredits, debit, refund


@pytest.fixture
def user(db):
    Tier.objects.get_or_create(
        slug="free",
        defaults={
            "name": "Free",
            "credits_per_period": 100,
            "max_upload_mb": 10,
            "max_rows": 50_000,
            "features": ["chat"],
            "is_default": True,
        },
    )
    ActionCost.objects.get_or_create(action="ai.chat_message", defaults={"cost": 3})
    return get_user_model().objects.create_user(email="test@example.com")


def test_debit_and_refund_idempotent(user):
    tx1 = debit(user, action="ai.chat_message", reference_id="job-1")
    assert tx1.amount == -3
    user.credit_account.refresh_from_db()
    bal = user.credit_account.balance

    tx2 = debit(user, action="ai.chat_message", reference_id="job-1")
    assert tx2.id == tx1.id
    user.credit_account.refresh_from_db()
    assert user.credit_account.balance == bal

    r1 = refund(user, action="ai.chat_message", reference_id="job-1")
    assert r1 is not None
    user.credit_account.refresh_from_db()
    assert user.credit_account.balance == bal + 3

    r2 = refund(user, action="ai.chat_message", reference_id="job-1")
    assert r2.id == r1.id


def test_insufficient_credits(user):
    user.credit_account.balance = 1
    user.credit_account.save()
    with pytest.raises(InsufficientCredits) as exc_info:
        debit(user, action="ai.chat_message", reference_id="job-x")
    err = exc_info.value
    assert err.required == 3
    assert err.balance == 1
    assert str(err) == (
        "Você não tem créditos suficientes para continuar. "
        "Esta ação precisa de 3 créditos e você tem 1."
    )
