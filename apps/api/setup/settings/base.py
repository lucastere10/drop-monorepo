from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from drop_ai.refs import parse_model_ref

from setup.env_contract import LOCAL_POSTGRES, resolve_drop_env
from setup.env_contract import profile as env_profile

# base.py → settings → setup → api → apps → repo root
_SETTINGS_FILE = Path(__file__).resolve()
BASE_DIR = _SETTINGS_FILE.parents[2]  # apps/api
REPO_ROOT = _SETTINGS_FILE.parents[4]  # monorepo root

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

DROP_ENV = resolve_drop_env()
_ENV = env_profile(DROP_ENV)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = False
ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "accounts",
    "core",
    "workers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "setup.middleware.CorrelationIdMiddleware",
]

ROOT_URLCONF = "setup.urls"
WSGI_APPLICATION = "setup.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        **LOCAL_POSTGRES,
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "OPTIONS": {},
    }
}

# hml/prod: Neon (or any Postgres URL) from Secret Manager
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DROP_ENV != "local" and DATABASE_URL:
    import urllib.parse as up

    u = up.urlparse(DATABASE_URL)
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": u.path.lstrip("/") or "drop",
        "USER": u.username or "",
        "PASSWORD": u.password or "",
        "HOST": u.hostname or "",
        "PORT": str(u.port or 5432),
        "OPTIONS": {"sslmode": "require"} if "neon.tech" in (u.hostname or "") else {},
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS: list[dict] = []

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "setup.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "14"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Drop API",
    "DESCRIPTION": "Drop — tabular file to understanding",
    "VERSION": "0.1.0",
}

CORS_ALLOWED_ORIGINS = (
    [_ENV["web_base_url"]] if _ENV["web_base_url"] else []
)
CORS_ALLOW_CREDENTIALS = True

# Ports — derived from DROP_ENV (ADR-013)
QUEUE_BACKEND = _ENV["queue"]
EMAIL_BACKEND_KIND = _ENV["email"]
STORAGE_BACKEND = _ENV["storage"]
LOCAL_STORAGE_ROOT = Path(os.getenv("LOCAL_STORAGE_ROOT", str(REPO_ROOT / "var" / "uploads")))

WEB_BASE_URL = _ENV["web_base_url"] or os.getenv("WEB_BASE_URL", "http://localhost:3000")
API_BASE_URL = _ENV["api_base_url"] or os.getenv("API_BASE_URL", "http://localhost:8000")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Drop <onboarding@resend.dev>")

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = (
    os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    or f"{WEB_BASE_URL.rstrip('/')}/auth/google/callback"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Refs are provider:model per use case (e.g. openai:gpt-4o-mini).
# Fallbacks live in drop_ai.refs.DEFAULT_FALLBACK_REFS, not env.
_LLM_PRIMARY_REF = "openai:gpt-5.6-luna"


def _llm_use(env_name: str, max_tokens: int | None = None) -> dict[str, Any]:
    provider, model = parse_model_ref(os.getenv(env_name, "") or _LLM_PRIMARY_REF)
    entry: dict[str, Any] = {
        "provider": provider,
        "model": model,
    }
    if max_tokens is not None:
        entry["max_tokens"] = max_tokens
    return entry


LLM_CONFIG = {
    "uses": {
        "overview": _llm_use("LLM_OVERVIEW", 2048),
        "insights": _llm_use("LLM_INSIGHTS", 4096),
        "chat": _llm_use("LLM_CHAT", 2048),
        "charts": _llm_use("LLM_CHARTS", 2048),
    },
}

# Cloud Tasks
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
CLOUD_TASKS_QUEUE = os.getenv("CLOUD_TASKS_QUEUE", "drop-jobs")
CLOUD_TASKS_SERVICE_ACCOUNT = os.getenv("CLOUD_TASKS_SERVICE_ACCOUNT", "")
INTERNAL_WORKER_TOKEN = os.getenv("INTERNAL_WORKER_TOKEN", "dev-internal-token")

MAGIC_LINK_TTL_MINUTES = int(os.getenv("MAGIC_LINK_TTL_MINUTES", "10"))
RATE_LIMIT_MAGIC_LINK_PER_HOUR = int(os.getenv("RATE_LIMIT_MAGIC_LINK_PER_HOUR", "5"))
RATE_LIMIT_ANON_UPLOAD_PER_HOUR = int(os.getenv("RATE_LIMIT_ANON_UPLOAD_PER_HOUR", "10"))
RATE_LIMIT_AUTH_UPLOAD_PER_HOUR = int(os.getenv("RATE_LIMIT_AUTH_UPLOAD_PER_HOUR", "30"))
RATE_LIMIT_AI_JOBS_PER_HOUR = int(os.getenv("RATE_LIMIT_AI_JOBS_PER_HOUR", "40"))
RATE_LIMIT_INTEREST_PER_HOUR = int(os.getenv("RATE_LIMIT_INTEREST_PER_HOUR", "5"))
ANONYMOUS_ANALYSIS_TTL_HOURS = int(os.getenv("ANONYMOUS_ANALYSIS_TTL_HOURS", "24"))
ANONYMOUS_MAX_UPLOAD_MB = int(os.getenv("ANONYMOUS_MAX_UPLOAD_MB", "5"))
ANONYMOUS_MAX_ROWS = int(os.getenv("ANONYMOUS_MAX_ROWS", "20000"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s correlation_id=%(correlation_id)s %(message)s",
        },
    },
    "filters": {
        "correlation": {
            "()": "setup.middleware.CorrelationIdFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "filters": ["correlation"],
        },
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
