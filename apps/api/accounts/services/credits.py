from __future__ import annotations

from django.db import transaction
from django.db.models import F

from accounts.models import ActionCost, CreditAccount, CreditTransaction, User


class InsufficientCredits(Exception):
    def __init__(
        self,
        message: str | None = None,
        *,
        required: int | None = None,
        balance: int | None = None,
    ):
        self.required = required
        self.balance = balance
        if message is None:
            message = _insufficient_message(required, balance)
        super().__init__(message)


def _credit_word(amount: int) -> str:
    return "crédito" if amount == 1 else "créditos"


def _insufficient_message(required: int | None, balance: int | None) -> str:
    base = "Você não tem créditos suficientes para continuar."
    if required is None or balance is None:
        return base
    return (
        f"{base} Esta ação precisa de {required} {_credit_word(required)} "
        f"e você tem {balance}."
    )


def get_action_cost(action: str) -> int:
    row = ActionCost.objects.filter(action=action).first()
    if row is None:
        raise ValueError(f"Unknown action cost: {action}")
    return row.cost


@transaction.atomic
def debit(
    user: User,
    *,
    action: str,
    amount: int | None = None,
    reference_id: str = "",
    meta: dict | None = None,
) -> CreditTransaction:
    if amount is None:
        amount = get_action_cost(action)
    if amount < 0:
        raise ValueError("debit amount must be >= 0")

    # idempotent debit for same reference
    if reference_id:
        existing = CreditTransaction.objects.filter(
            reference_id=reference_id, tx_type=CreditTransaction.TxType.DEBIT, action=action
        ).first()
        if existing:
            return existing

    account = CreditAccount.objects.select_for_update().get(user=user)
    if account.balance < amount:
        raise InsufficientCredits(required=amount, balance=account.balance)
    account.balance = F("balance") - amount
    account.save(update_fields=["balance", "updated_at"])
    account.refresh_from_db()
    return CreditTransaction.objects.create(
        user=user,
        amount=-amount,
        tx_type=CreditTransaction.TxType.DEBIT,
        action=action,
        balance_after=account.balance,
        reference_id=reference_id,
        meta=meta or {},
    )


@transaction.atomic
def refund(
    user: User,
    *,
    action: str,
    reference_id: str,
    meta: dict | None = None,
) -> CreditTransaction | None:
    """Refund once for a prior debit with the same reference_id."""
    if not reference_id:
        raise ValueError("reference_id required for refund")
    existing_refund = CreditTransaction.objects.filter(
        reference_id=reference_id, tx_type=CreditTransaction.TxType.REFUND, action=action
    ).first()
    if existing_refund:
        return existing_refund

    debit_tx = CreditTransaction.objects.filter(
        reference_id=reference_id, tx_type=CreditTransaction.TxType.DEBIT, action=action
    ).first()
    if debit_tx is None:
        return None

    amount = abs(debit_tx.amount)
    account = CreditAccount.objects.select_for_update().get(user=user)
    account.balance = F("balance") + amount
    account.save(update_fields=["balance", "updated_at"])
    account.refresh_from_db()
    return CreditTransaction.objects.create(
        user=user,
        amount=amount,
        tx_type=CreditTransaction.TxType.REFUND,
        action=action,
        balance_after=account.balance,
        reference_id=reference_id,
        meta=meta or {},
    )


@transaction.atomic
def credit(
    user: User,
    *,
    amount: int,
    action: str = "admin.adjust",
    period_key: str = "",
    reference_id: str = "",
    tx_type: str = CreditTransaction.TxType.CREDIT,
    meta: dict | None = None,
) -> CreditTransaction:
    if period_key:
        existing = CreditTransaction.objects.filter(
            user=user, period_key=period_key, action=action
        ).first()
        if existing:
            return existing
    account = CreditAccount.objects.select_for_update().get(user=user)
    account.balance = F("balance") + amount
    account.save(update_fields=["balance", "updated_at"])
    account.refresh_from_db()
    return CreditTransaction.objects.create(
        user=user,
        amount=amount,
        tx_type=tx_type,
        action=action,
        balance_after=account.balance,
        reference_id=reference_id,
        period_key=period_key,
        meta=meta or {},
    )


@transaction.atomic
def adjust_balance(user: User, *, delta: int, meta: dict | None = None) -> CreditTransaction:
    account = CreditAccount.objects.select_for_update().get(user=user)
    new_balance = account.balance + delta
    if new_balance < 0:
        raise InsufficientCredits("adjust would make balance negative")
    account.balance = new_balance
    account.save(update_fields=["balance", "updated_at"])
    return CreditTransaction.objects.create(
        user=user,
        amount=delta,
        tx_type=CreditTransaction.TxType.ADJUST,
        action="admin.adjust",
        balance_after=account.balance,
        meta=meta or {},
    )
