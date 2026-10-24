import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from core.models import ProductInterest


@pytest.mark.django_db
def test_create_product_interest():
    client = APIClient()
    res = client.post(
        "/api/interests/",
        {
            "name": "Ana",
            "email": "ana@example.com",
            "interests": ["charts", "ml"],
            "comment": "Quero prever vendas",
        },
        format="json",
    )
    assert res.status_code == 201
    saved = ProductInterest.objects.get()
    assert saved.name == "Ana"
    assert saved.email == "ana@example.com"
    assert saved.interests == ["charts", "ml"]
    assert saved.comment == "Quero prever vendas"


@pytest.mark.django_db
def test_reject_empty_email():
    client = APIClient()
    res = client.post(
        "/api/interests/",
        {"name": "Ana", "email": "", "interests": ["chat"]},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["code"] == "invalid"
    assert ProductInterest.objects.count() == 0


@pytest.mark.django_db
def test_reject_unknown_interest():
    client = APIClient()
    res = client.post(
        "/api/interests/",
        {"name": "Ana", "email": "ana@example.com", "interests": ["billing"]},
        format="json",
    )
    assert res.status_code == 400
    assert res.json()["code"] == "invalid"
    assert ProductInterest.objects.count() == 0


@override_settings(RATE_LIMIT_INTEREST_PER_HOUR=1)
@pytest.mark.django_db
def test_interest_rate_limit():
    client = APIClient()
    payload = {"name": "Ana", "email": "ana@example.com", "interests": ["insights"]}
    first = client.post("/api/interests/", payload, format="json")
    second = client.post("/api/interests/", payload, format="json")
    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"
