from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CreditAccount, Tier, User


@receiver(post_save, sender=User)
def ensure_credit_account(sender, instance: User, created: bool, **kwargs):
    if not created:
        return
    tier = Tier.objects.filter(is_default=True).first() or Tier.objects.filter(slug="free").first()
    if tier is None:
        tier = Tier.objects.create(
            slug="free",
            name="Free",
            credits_per_period=100,
            max_upload_mb=10,
            max_rows=50_000,
            features=["chat", "overview", "insights"],
            is_default=True,
        )
    CreditAccount.objects.get_or_create(
        user=instance,
        defaults={"tier": tier, "balance": tier.credits_per_period},
    )
