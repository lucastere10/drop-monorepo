import os

from .base import *

DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

# Cloud Run terminates TLS and forwards HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


def _csrf_origins(*urls: str) -> list[str]:
    origins: list[str] = []
    for raw in urls:
        value = (raw or "").strip().rstrip("/")
        if value.startswith("https://") or value.startswith("http://"):
            origins.append(value)
    return origins


CSRF_TRUSTED_ORIGINS = _csrf_origins(WEB_BASE_URL, API_BASE_URL)
extra_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if extra_csrf:
    CSRF_TRUSTED_ORIGINS = list(
        dict.fromkeys(CSRF_TRUSTED_ORIGINS + _csrf_origins(*extra_csrf.split(",")))
    )
