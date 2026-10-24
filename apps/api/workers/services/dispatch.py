from __future__ import annotations

from django.db import transaction

from accounts.services.credits import debit
from core.models import Analysis
from workers.models import Job
from workers.services.queue import get_queue


@transaction.atomic
def enqueue_job(
    *,
    user,
    job_type: str,
    payload: dict,
    credit_action: str,
    analysis: Analysis | None = None,
    charge: bool = True,
) -> Job:
    job = Job.objects.create(
        user=user,
        analysis=analysis,
        job_type=job_type,
        payload=payload,
        credit_action=credit_action or "",
        status=Job.Status.QUEUED,
    )
    if charge and user is not None and credit_action:
        debit(user, action=credit_action, reference_id=str(job.id))
        job.credits_debited = True
        job.save(update_fields=["credits_debited"])
    job_id = str(job.id)

    def _dispatch():
        get_queue().enqueue(Job.objects.get(pk=job_id))

    transaction.on_commit(_dispatch)
    return job
