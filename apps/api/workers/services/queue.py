from __future__ import annotations

import json
import logging
from typing import Protocol

from django.conf import settings

from workers.models import Job

logger = logging.getLogger(__name__)


class QueueBackend(Protocol):
    def enqueue(self, job: Job) -> None: ...


class InlineQueueBackend:
    def enqueue(self, job: Job) -> None:
        from workers.services.runner import run_job

        try:
            run_job(str(job.id))
        except Exception:
            # Never fail the producer request because a follow-up job crashed.
            logger.exception("inline queue job crashed job_id=%s type=%s", job.id, job.job_type)


class CloudTasksQueueBackend:
    def enqueue(self, job: Job) -> None:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(
            settings.GCP_PROJECT, settings.GCP_LOCATION, settings.CLOUD_TASKS_QUEUE
        )
        url = f"{settings.API_BASE_URL}/internal/workers/{job.job_type}/"
        payload = json.dumps({"job_id": str(job.id)}).encode()
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Token": settings.INTERNAL_WORKER_TOKEN,
                },
                "body": payload,
            }
        }
        if settings.CLOUD_TASKS_SERVICE_ACCOUNT:
            task["http_request"]["oidc_token"] = {
                "service_account_email": settings.CLOUD_TASKS_SERVICE_ACCOUNT
            }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued cloud task job_id=%s type=%s", job.id, job.job_type)


def get_queue() -> QueueBackend:
    if settings.QUEUE_BACKEND == "cloud_tasks":
        return CloudTasksQueueBackend()
    return InlineQueueBackend()
