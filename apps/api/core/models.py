from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class UploadedFile(models.Model):
    class Status(models.TextChoices):
        STORED = "stored", "Stored"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.BigIntegerField()
    storage_key = models.CharField(max_length=512)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.STORED)
    created_at = models.DateTimeField(auto_now_add=True)


class Analysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analyses",
        null=True,
        blank=True,
    )
    uploaded_file = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE, related_name="analyses"
    )
    title = models.CharField(max_length=200)
    summary = models.JSONField(default=dict)
    n_rows = models.IntegerField(default=0)
    n_cols = models.IntegerField(default=0)
    quality_score = models.FloatField(null=True, blank=True)
    quality_grade = models.CharField(max_length=1, blank=True)
    is_favorite = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, db_index=True)
    overview_text = models.TextField(blank=True)
    overview_job_id = models.UUIDField(null=True, blank=True)
    dashboard_layout = models.JSONField(default=dict, blank=True)
    dashboard_job_id = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_anonymous(self) -> bool:
        return self.user_id is None

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and timezone.now() > self.expires_at)

    def ensure_share_token(self) -> str:
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(24)
            self.save(update_fields=["share_token"])
        return self.share_token

    @staticmethod
    def anonymous_expiry():
        hours = getattr(settings, "ANONYMOUS_ANALYSIS_TTL_HOURS", 24)
        return timezone.now() + timedelta(hours=hours)


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Insight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="insights")
    kind = models.CharField(max_length=64, default="general")
    content = models.TextField()
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ChartSpec(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="charts")
    title = models.CharField(max_length=200, blank=True)
    chart_type = models.CharField(max_length=64, default="bar")
    spec = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    interests = models.JSONField(default=list)
    comment = models.TextField(blank=True)
    analysis_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RateLimitEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=32, db_index=True)
    key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["scope", "key", "created_at"]),
        ]

