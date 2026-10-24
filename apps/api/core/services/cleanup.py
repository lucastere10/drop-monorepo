from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from core.models import Analysis, UploadedFile
from core.services.storage import get_storage


def cleanup_expired_uploads(*, days: int = 30) -> int:
    """Delete expired anonymous analyses and stale upload files. Returns deleted count."""
    storage = get_storage()
    deleted = 0

    expired = Analysis.objects.filter(user__isnull=True, expires_at__lt=timezone.now())
    for analysis in expired.select_related("uploaded_file"):
        key = analysis.uploaded_file.storage_key
        analysis.delete()
        try:
            storage.delete(key)
        except Exception:  # noqa: BLE001
            pass
        deleted += 1

    cutoff = timezone.now() - timedelta(days=days)
    for uf in UploadedFile.objects.filter(created_at__lt=cutoff):
        has_public = uf.analyses.filter(is_public=True).exists()
        if has_public:
            continue
        if uf.analyses.exists() and uf.user_id is not None:
            continue
        try:
            storage.delete(uf.storage_key)
        except Exception:  # noqa: BLE001
            pass
        uf.delete()
        deleted += 1

    root = Path(settings.LOCAL_STORAGE_ROOT)
    if root.exists():
        keys = set(UploadedFile.objects.values_list("storage_key", flat=True))
        for path in root.iterdir():
            if path.is_file() and path.name not in keys:
                path.unlink(missing_ok=True)

    return deleted
