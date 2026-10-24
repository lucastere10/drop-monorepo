from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )
    analysis = models.ForeignKey(
        "core.Analysis",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="jobs",
    )
    job_type = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    credit_action = models.CharField(max_length=64, blank=True)
    credits_debited = models.BooleanField(default=False)
    credits_refunded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
