from __future__ import annotations

import os
from typing import Literal, TypedDict

DropEnv = Literal["local", "hml", "prod"]

VALID_ENVS: frozenset[str] = frozenset({"local", "hml", "prod"})

SETTINGS_MODULE: dict[str, str] = {
    "local": "setup.settings.development",
    "hml": "setup.settings.staging",
    "prod": "setup.settings.production",
}

LOCAL_POSTGRES = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "drop",
    "USER": "drop",
    "PASSWORD": "drop",
    "PORT": "5432",
}


class EnvProfile(TypedDict):
    queue: str
    email: str
    storage: str
    web_base_url: str
    api_base_url: str


_PROFILES: dict[str, EnvProfile] = {
    "local": {
        "queue": "inline",
        "email": "console",
        "storage": "local",
        "web_base_url": "http://localhost:3000",
        "api_base_url": "http://localhost:8000",
    },
    "hml": {
        "queue": "cloud_tasks",
        "email": "resend",
        "storage": "local",
        "web_base_url": "",
        "api_base_url": "",
    },
    "prod": {
        "queue": "cloud_tasks",
        "email": "resend",
        "storage": "local",
        "web_base_url": "",
        "api_base_url": "",
    },
}


def resolve_drop_env(raw: str | None = None) -> DropEnv:
    value = (raw if raw is not None else os.getenv("DROP_ENV", "local")).strip().lower()
    if value not in VALID_ENVS:
        raise ValueError(f"Invalid DROP_ENV {value!r}; expected local, hml, or prod")
    return value  # type: ignore[return-value]


def django_settings_module(env: str | None = None) -> str:
    return SETTINGS_MODULE[resolve_drop_env(env)]


def profile(env: str | None = None) -> EnvProfile:
    resolved = resolve_drop_env(env)
    base = dict(_PROFILES[resolved])
    if resolved != "local":
        web = os.getenv("WEB_BASE_URL", "").strip()
        api = os.getenv("API_BASE_URL", "").strip()
        if web:
            base["web_base_url"] = web
        if api:
            base["api_base_url"] = api
    return base  # type: ignore[return-value]
