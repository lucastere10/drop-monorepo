from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email: str, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        user = self.create_user(email, **extra)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email


class SocialAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    provider = models.CharField(max_length=32)  # google
    provider_subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("provider", "provider_subject")


class MagicLinkToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    request_ip = models.GenericIPAddressField(null=True, blank=True)

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and timezone.now() < self.expires_at


class Tier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=64)
    credits_per_period = models.PositiveIntegerField(default=100)
    max_upload_mb = models.PositiveIntegerField(default=10)
    max_rows = models.PositiveIntegerField(default=50_000)
    features = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.slug


class CreditAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credit_account")
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name="accounts")
    balance = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class CreditTransaction(models.Model):
    class TxType(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"
        ADJUST = "adjust", "Adjust"
        REFUND = "refund", "Refund"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credit_transactions")
    amount = models.IntegerField()  # signed: debit negative or positive with type
    tx_type = models.CharField(max_length=16, choices=TxType.choices)
    action = models.CharField(max_length=64, blank=True)
    balance_after = models.IntegerField()
    reference_id = models.CharField(max_length=64, blank=True, db_index=True)
    period_key = models.CharField(max_length=64, blank=True, db_index=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period_key", "action"],
                condition=~models.Q(period_key=""),
                name="uniq_renew_period",
            ),
            models.UniqueConstraint(
                fields=["reference_id", "tx_type", "action"],
                condition=~models.Q(reference_id=""),
                name="uniq_tx_reference_action_type",
            ),
        ]


class ActionCost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=64, unique=True)
    cost = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.action}={self.cost}"
