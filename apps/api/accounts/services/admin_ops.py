from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Sum

from accounts.models import CreditAccount, Tier, User
from accounts.services.credits import InsufficientCredits, adjust_balance
from core.models import Analysis
from workers.models import Job


class AdminOpsError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def parse_limit(raw: str | None, *, default: int = 50, maximum: int = 100) -> int:
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value < 1:
        return default
    return min(value, maximum)


def _user_queryset():
    return User.objects.select_related("credit_account__tier").annotate(
        analysis_count=Count("analyses")
    )


def serialize_user(user: User) -> dict:
    account = getattr(user, "credit_account", None)
    count = getattr(user, "analysis_count", None)
    if count is None:
        count = user.analyses.count()
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "last_login": user.last_login,
        "date_joined": user.date_joined,
        "tier": account.tier.slug if account else None,
        "balance": account.balance if account else 0,
        "analysis_count": count,
    }


def overview() -> dict:
    job_counts = {status: 0 for status in Job.Status.values}
    for row in Job.objects.values("status").annotate(n=Count("id")):
        job_counts[row["status"]] = row["n"]
    balance_sum = CreditAccount.objects.aggregate(total=Sum("balance"))["total"] or 0
    tiers = [
        {"slug": tier.slug, "name": tier.name}
        for tier in Tier.objects.order_by("slug")
    ]
    return {
        "users_total": User.objects.count(),
        "users_active": User.objects.filter(is_active=True).count(),
        "analyses_total": Analysis.objects.count(),
        "analyses_anonymous": Analysis.objects.filter(user__isnull=True).count(),
        "jobs_by_status": job_counts,
        "credits_balance_sum": balance_sum,
        "tiers": tiers,
    }


def list_users(*, limit: int) -> list[dict]:
    return [serialize_user(user) for user in _user_queryset().order_by("-date_joined")[:limit]]


def list_analyses(*, limit: int) -> list[dict]:
    rows = Analysis.objects.select_related("user").order_by("-created_at")[:limit]
    return [
        {
            "id": str(row.id),
            "title": row.title,
            "user_email": row.user.email if row.user_id else None,
            "is_anonymous": row.user_id is None,
            "n_rows": row.n_rows,
            "n_cols": row.n_cols,
            "created_at": row.created_at,
            "expires_at": row.expires_at,
        }
        for row in rows
    ]


def _get_user(user_id) -> User:
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise AdminOpsError("not_found", "Usuário não encontrado.", status=404) from exc


@transaction.atomic
def update_user(
    actor: User,
    user_id,
    *,
    is_active: bool | None = None,
    tier_slug: str | None = None,
    is_staff: bool | None = None,
) -> dict:
    target = _get_user(user_id)
    if is_staff is not None and not actor.is_superuser:
        raise AdminOpsError(
            "forbidden",
            "Só um superusuário pode alterar staff.",
            status=403,
        )
    if is_active is False and target.id == actor.id:
        raise AdminOpsError(
            "cannot_deactivate_self",
            "Você não pode desativar a própria conta.",
        )

    update_fields: list[str] = []
    if is_staff is not None:
        target.is_staff = is_staff
        update_fields.append("is_staff")
    if is_active is not None:
        target.is_active = is_active
        update_fields.append("is_active")
    if update_fields:
        target.save(update_fields=update_fields)

    if tier_slug is not None:
        try:
            tier = Tier.objects.get(slug=tier_slug)
        except Tier.DoesNotExist as exc:
            raise AdminOpsError("unknown_tier", "Tier desconhecido.") from exc
        try:
            account = CreditAccount.objects.select_for_update().get(user=target)
        except CreditAccount.DoesNotExist as exc:
            raise AdminOpsError("no_account", "Usuário sem conta de créditos.") from exc
        account.tier = tier
        account.save(update_fields=["tier", "updated_at"])

    return serialize_user(_user_queryset().get(pk=target.pk))


@transaction.atomic
def adjust_user_credits(actor: User, user_id, *, delta: int, reason: str) -> dict:
    target = _get_user(user_id)
    try:
        tx = adjust_balance(
            target,
            delta=delta,
            meta={"admin": actor.email, "reason": reason},
        )
    except InsufficientCredits as exc:
        raise AdminOpsError(
            "insufficient_credits",
            "O ajuste deixaria o saldo negativo.",
        ) from exc
    except CreditAccount.DoesNotExist as exc:
        raise AdminOpsError("no_account", "Usuário sem conta de créditos.") from exc
    return {
        "id": str(tx.id),
        "amount": tx.amount,
        "tx_type": tx.tx_type,
        "action": tx.action,
        "balance_after": tx.balance_after,
        "reason": reason,
    }
