from django.urls import path

from workers.views import InternalWorkerView


class _Overview(InternalWorkerView):
    job_type = "ai_overview"


class _Insights(InternalWorkerView):
    job_type = "ai_insights"


class _Chat(InternalWorkerView):
    job_type = "ai_chat"


class _Charts(InternalWorkerView):
    job_type = "ai_charts"


class _CronRenew(InternalWorkerView):
    job_type = "cron_renew_credits"


class _CronCleanup(InternalWorkerView):
    job_type = "cron_cleanup_uploads"


urlpatterns = [
    path("ai_overview/", _Overview.as_view()),
    path("ai_insights/", _Insights.as_view()),
    path("ai_chat/", _Chat.as_view()),
    path("ai_charts/", _Charts.as_view()),
    path("cron_renew_credits/", _CronRenew.as_view()),
    path("cron_cleanup_uploads/", _CronCleanup.as_view()),
]
