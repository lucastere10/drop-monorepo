import pytest
from rest_framework.test import APIClient

from accounts.models import User
from setup.env_contract import django_settings_module, profile, resolve_drop_env


def test_resolve_drop_env_defaults_local(monkeypatch):
    monkeypatch.delenv("DROP_ENV", raising=False)
    assert resolve_drop_env() == "local"


def test_local_profile_ports():
    p = profile("local")
    assert p["queue"] == "inline"
    assert p["email"] == "console"
    assert p["storage"] == "local"
    assert django_settings_module("local") == "setup.settings.development"
    assert django_settings_module("hml") == "setup.settings.staging"
    assert django_settings_module("prod") == "setup.settings.production"


def test_invalid_drop_env():
    with pytest.raises(ValueError):
        resolve_drop_env("staging")


@pytest.fixture
def api():
    return APIClient()


def test_auth_methods_without_google(api, settings):
    settings.GOOGLE_OAUTH_CLIENT_ID = ""
    settings.GOOGLE_OAUTH_CLIENT_SECRET = ""
    resp = api.get("/api/auth/methods/")
    assert resp.status_code == 200
    assert resp.json()["methods"] == ["magic_link"]


def test_auth_methods_with_google(api, settings):
    settings.GOOGLE_OAUTH_CLIENT_ID = "client-id"
    settings.GOOGLE_OAUTH_CLIENT_SECRET = "client-secret"
    resp = api.get("/api/auth/methods/")
    assert resp.json()["methods"] == ["magic_link", "google"]


def test_magic_link_local_returns_dev_url(api, db, settings):
    settings.DROP_ENV = "local"
    resp = api.post("/api/auth/magic-link/", {"email": "dev@example.com"}, format="json")
    assert resp.status_code == 200
    url = resp.json()["dev_verify_url"]
    assert "/auth/verify?token=" in url


def test_magic_link_prod_has_no_dev_url(api, db, settings):
    settings.DROP_ENV = "prod"
    resp = api.post("/api/auth/magic-link/", {"email": "prod@example.com"}, format="json")
    assert resp.status_code == 204
    assert resp.content == b""


def test_magic_link_sets_last_login(api, db, settings):
    settings.DROP_ENV = "local"
    resp = api.post("/api/auth/magic-link/", {"email": "seen@example.com"}, format="json")
    token = resp.json()["dev_verify_url"].split("token=", 1)[1]
    verified = api.post("/api/auth/magic-link/verify/", {"token": token}, format="json")
    assert verified.status_code == 200
    user = User.objects.get(email="seen@example.com")
    assert user.last_login is not None
