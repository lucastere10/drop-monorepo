from __future__ import annotations

from django.db import transaction

from core.models import Analysis


class ClaimError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@transaction.atomic
def claim_anonymous_analysis(*, user, analysis: Analysis) -> Analysis:
    """Transfer an anonymous (unexpired) analysis to the authenticated user."""
    locked = Analysis.objects.select_for_update().filter(pk=analysis.pk).first()
    if locked is None:
        raise ClaimError("not_found", "Análise não encontrada.")
    if locked.is_expired:
        raise ClaimError("expired", "Esta análise anônima expirou.")
    if locked.user_id is not None:
        if locked.user_id == user.id:
            return locked
        raise ClaimError("already_owned", "Esta análise já pertence a outra conta.")

    locked.user = user
    locked.expires_at = None
    locked.save(update_fields=["user", "expires_at", "updated_at"])

    uf = locked.uploaded_file
    if uf.user_id is None:
        uf.user = user
        uf.save(update_fields=["user"])

    return locked
