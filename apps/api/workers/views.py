from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from workers.models import Job
from workers.services.runner import run_job

CRON_TYPES_WITHOUT_JOB_ID = frozenset({"cron_renew_credits", "cron_cleanup_uploads"})


class JobDetailView(APIView):
    """Authenticated owners or anonymous jobs (user null) are readable by id."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        job = Job.objects.filter(pk=pk).first()
        if not job:
            return Response(
                {"code": "not_found", "message": "Job não encontrado.", "details": {}},
                status=404,
            )
        if job.user_id and (
            not request.user.is_authenticated or request.user.id != job.user_id
        ):
            return Response(
                {"code": "forbidden", "message": "Acesso negado.", "details": {}},
                status=403,
            )
        return Response(
            {
                "id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "result": job.result,
                "error": job.error,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }
        )


class InternalWorkerView(APIView):
    permission_classes = [AllowAny]
    job_type: str = ""

    def post(self, request, *args, **kwargs):
        token = request.headers.get("X-Internal-Token")
        if token != settings.INTERNAL_WORKER_TOKEN:
            return Response(
                {"code": "forbidden", "message": "Invalid internal token.", "details": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        job_id = request.data.get("job_id")
        if not job_id and self.job_type in CRON_TYPES_WITHOUT_JOB_ID:
            job_user = None
            if self.job_type == "cron_renew_credits":
                from accounts.models import User

                job_user = User.objects.filter(is_staff=True).first() or User.objects.first()
                if job_user is None:
                    return Response(
                        {"code": "no_user", "message": "No user for cron"},
                        status=400,
                    )
            job = Job.objects.create(
                user=job_user,
                job_type=self.job_type,
                payload={},
                status=Job.Status.QUEUED,
            )
            job_id = str(job.id)
        if not job_id:
            return Response(
                {"code": "missing_job_id", "message": "job_id required", "details": {}},
                status=400,
            )
        run_job(job_id)
        job = Job.objects.get(pk=job_id)
        return Response({"job_id": job_id, "status": job.status})
