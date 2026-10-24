from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CreditAccount
from accounts.services.credits import credit


class Command(BaseCommand):
    help = "Renew credits for all accounts (idempotent per YYYY-MM)"

    def handle(self, *args, **options):
        period_key = timezone.now().strftime("%Y-%m")
        count = 0
        for account in CreditAccount.objects.select_related("user", "tier").all():
            credit(
                account.user,
                amount=account.tier.credits_per_period,
                action="credits.renew",
                period_key=period_key,
                meta={"period": period_key},
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Renewed {count} accounts for {period_key}"))
