from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from core.models import RateLimitEvent
from setup.http import client_ip
from workers.models import Job

AI_JOB_TYPES = ("ai_overview", "ai_insights", "ai_chat", "ai_charts")

RATE_LIMIT_MESSAGE = "Muitas solicitações. Tente mais tarde."


class RateLimited(Exception):
    def __init__(self, message: str = RATE_LIMIT_MESSAGE):
        self.code = "rate_limited"
        self.message = message
        super().__init__(message)


def check_and_hit(*, scope: str, key: str, limit: int) -> None:
    if limit <= 0 or not key:
        return
    since = timezone.now() - timedelta(hours=1)
    used = RateLimitEvent.objects.filter(scope=scope, key=key, created_at__gte=since).count()
    if used >= limit:
        raise RateLimited()
    RateLimitEvent.objects.create(scope=scope, key=key)


def check_upload(request) -> None:
    if request.user.is_authenticated:
        check_and_hit(
            scope="auth_upload",
            key=str(request.user.id),
            limit=int(settings.RATE_LIMIT_AUTH_UPLOAD_PER_HOUR),
        )
        return
    ip = client_ip(request) or "unknown"
    check_and_hit(
        scope="anon_upload",
        key=ip,
        limit=int(settings.RATE_LIMIT_ANON_UPLOAD_PER_HOUR),
    )


def check_interest(request) -> None:
    ip = client_ip(request) or "unknown"
    check_and_hit(
        scope="interest",
        key=ip,
        limit=int(settings.RATE_LIMIT_INTEREST_PER_HOUR),
    )


def check_ai_jobs(user) -> None:
    limit = int(settings.RATE_LIMIT_AI_JOBS_PER_HOUR)
    if limit <= 0 or user is None:
        return
    since = timezone.now() - timedelta(hours=1)
    used = Job.objects.filter(
        user=user,
        job_type__in=AI_JOB_TYPES,
        created_at__gte=since,
    ).count()
    if used >= limit:
        raise RateLimited()
