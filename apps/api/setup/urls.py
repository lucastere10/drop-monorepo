
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health(_request):
    from django.db import connection

    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok}, status=status)


urlpatterns = [
    path("health/", health),
    path("admin/", __import__("django.contrib.admin", fromlist=["site"]).site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/auth/", include("accounts.urls_auth")),
    path("api/credits/", include("accounts.urls_credits")),
    path("api/admin/", include("accounts.urls_admin")),
    path("api/", include("core.urls")),
    path("internal/workers/", include("workers.urls")),
]
