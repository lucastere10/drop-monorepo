from __future__ import annotations

from django.conf import settings
from django.db import transaction

from accounts.services.credits import InsufficientCredits, debit
from core.models import Analysis, UploadedFile
from core.services.cleaning import clean_dataframe
from core.services.deterministic_charts import save_deterministic_charts
from core.services.ingest import read_dataframe
from core.services.profiling import profile_dataframe
from core.services.storage import get_storage


def _credits_ingest_error(exc: InsufficientCredits) -> IngestError:
    details = {}
    if exc.required is not None and exc.balance is not None:
        details = {"required": exc.required, "balance": exc.balance}
    return IngestError("insufficient_credits", str(exc), details)


class IngestError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def load_stored_dataframe(storage_key: str, *, original_name: str = ""):
    """Read a stored file and apply the same cleaning used at upload."""
    storage = get_storage()
    try:
        path = storage.open(storage_key)
    except FileNotFoundError:
        finder = getattr(storage, "find_unique_named", None)
        path = finder(original_name) if finder and original_name else None
        if path is None:
            raise ValueError(
                "O arquivo original não está mais disponível. "
                "Envie o CSV novamente para montar o dashboard."
            ) from None
    df = read_dataframe(path)
    return clean_dataframe(df)


def load_analysis_dataframe(analysis: Analysis):
    uploaded = analysis.uploaded_file
    df, _cleaning = load_stored_dataframe(
        uploaded.storage_key,
        original_name=uploaded.original_name,
    )
    return df


def _tier_limits(user):
    if user is not None and hasattr(user, "credit_account"):
        tier = user.credit_account.tier
        return tier.max_upload_mb, tier.max_rows
    return (
        int(getattr(settings, "ANONYMOUS_MAX_UPLOAD_MB", 5)),
        int(getattr(settings, "ANONYMOUS_MAX_ROWS", 20_000)),
    )


@transaction.atomic
def create_analysis_from_upload(*, user, uploaded) -> Analysis:
    max_upload_mb, max_rows = _tier_limits(user)
    name = uploaded.name
    size = uploaded.size
    max_bytes = max_upload_mb * 1024 * 1024
    if size > max_bytes:
        raise IngestError("file_too_large", f"Arquivo excede {max_upload_mb} MB.")

    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in {"csv", "xlsx", "xls", "json"}:
        raise IngestError("unsupported_format", "Use CSV, XLSX ou JSON.")

    storage = get_storage()
    key = storage.save(filename=name, stream=uploaded.file)
    uf = UploadedFile.objects.create(
        user=user if user is not None and getattr(user, "is_authenticated", False) else None,
        original_name=name,
        content_type=getattr(uploaded, "content_type", "") or "",
        size_bytes=size,
        storage_key=key,
        status=UploadedFile.Status.STORED,
    )
    try:
        df, cleaning = load_stored_dataframe(key)
    except Exception as exc:
        uf.status = UploadedFile.Status.FAILED
        uf.save(update_fields=["status"])
        raise IngestError("read_failed", f"Falha ao ler arquivo: {exc}") from exc

    if len(df) > max_rows:
        raise IngestError("too_many_rows", f"Máximo de {max_rows} linhas no seu plano.")

    summary = profile_dataframe(df, cleaning=cleaning)

    owner = user if user is not None and getattr(user, "is_authenticated", False) else None
    starting_balance = owner.credit_account.balance if owner is not None else None
    if owner is not None:
        try:
            debit(owner, action="analysis.upload", reference_id=str(uf.id))
        except InsufficientCredits as exc:
            raise _credits_ingest_error(exc) from exc

    title = name.rsplit(".", 1)[0][:120]
    analysis = Analysis.objects.create(
        user=owner,
        uploaded_file=uf,
        title=title,
        summary=summary,
        n_rows=summary["n_rows"],
        n_cols=summary["n_cols"],
        quality_score=summary.get("quality_score"),
        quality_grade=summary.get("quality_grade") or "",
        overview_text=summary.get("text_summary") or "",
        expires_at=None if owner else Analysis.anonymous_expiry(),
    )
    uf.status = UploadedFile.Status.PROCESSED
    uf.save(update_fields=["status"])

    # Real charts from profile data (no LLM / no credits)
    save_deterministic_charts(analysis, df, summary=summary)

    # Auto-enqueue overview LLM (after commit via dispatch)
    from workers.services.dispatch import enqueue_job

    try:
        job = enqueue_job(
            user=owner,
            job_type="ai_overview",
            payload={"analysis_id": str(analysis.id)},
            credit_action="ai.overview" if owner else "",
            analysis=analysis,
            charge=bool(owner),
        )
    except InsufficientCredits as exc:
        # Upload debit is in this transaction and rolls back with the error.
        reported = InsufficientCredits(
            required=exc.required,
            balance=starting_balance if starting_balance is not None else exc.balance,
        )
        raise _credits_ingest_error(reported) from exc
    analysis.overview_job_id = job.id
    analysis.save(update_fields=["overview_job_id"])
    return analysis
