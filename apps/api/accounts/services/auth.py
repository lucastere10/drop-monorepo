from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

import httpx
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import MagicLinkToken, SocialAccount, User
from notifications.email import get_email_backend
from setup.http import client_ip


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def issue_tokens(user: User) -> dict:
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }


def request_magic_link(email: str, *, request=None) -> str:
    email = email.strip().lower()
    ip = client_ip(request) if request is not None else None
    since = timezone.now() - timedelta(hours=1)
    qs = MagicLinkToken.objects.filter(email=email, created_at__gte=since)
    if qs.count() >= settings.RATE_LIMIT_MAGIC_LINK_PER_HOUR:
        raise AuthError("rate_limited", "Muitas solicitações. Tente mais tarde.")

    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    MagicLinkToken.objects.create(
        email=email,
        token=token_hash,
        expires_at=timezone.now() + timedelta(minutes=settings.MAGIC_LINK_TTL_MINUTES),
        request_ip=ip,
    )
    link = f"{settings.WEB_BASE_URL}/auth/verify?token={raw}"
    get_email_backend().send(
        to=email,
        subject="Seu link de acesso Drop",
        html=f"<p>Acesse o Drop:</p><p><a href=\"{link}\">{link}</a></p><p>Expira em {settings.MAGIC_LINK_TTL_MINUTES} minutos.</p>",
        text=f"Acesse o Drop: {link}",
    )
    return link


def verify_magic_link(raw_token: str) -> dict:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    row = MagicLinkToken.objects.filter(token=token_hash).first()
    if row is None or not row.is_valid:
        raise AuthError("invalid_token", "Link inválido ou expirado.")
    row.used_at = timezone.now()
    row.save(update_fields=["used_at"])
    user, _ = User.objects.get_or_create(email=row.email.lower())
    return issue_tokens(user)


def available_auth_methods() -> list[str]:
    methods = ["magic_link"]
    if settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET:
        methods.append("google")
    return methods


def google_start() -> dict:
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        raise AuthError("oauth_not_configured", "Google OAuth não configurado.")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
        "prompt": "select_account",
    }
    from urllib.parse import urlencode

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"authorization_url": url, "state": state}


def google_callback(*, code: str, state: str) -> dict:  # state validated by BFF
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        raise AuthError("oauth_not_configured", "Google OAuth não configurado.")
    with httpx.Client(timeout=20) as client:
        token_resp = client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        access = token_resp.json()["access_token"]
        info = client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        info.raise_for_status()
        payload = info.json()
    email = (payload.get("email") or "").lower()
    sub = payload.get("sub")
    if not email or not sub:
        raise AuthError("oauth_failed", "Não foi possível obter email do Google.")
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": payload.get("given_name") or "",
            "last_name": payload.get("family_name") or "",
        },
    )
    SocialAccount.objects.get_or_create(
        provider="google", provider_subject=sub, defaults={"user": user}
    )
    return issue_tokens(user)
