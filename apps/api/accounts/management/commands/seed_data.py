from django.core.management.base import BaseCommand

from accounts.models import ActionCost, Tier

DEFAULT_COSTS = [
    ("analysis.upload", 1, "Upload e profiling"),
    ("ai.overview", 5, "Overview em linguagem natural"),
    ("ai.insights", 10, "Geração de insights"),
    ("ai.chart", 8, "Geração de gráfico"),
    ("ai.dashboard", 15, "Dashboard de gráficos"),
    ("ai.chat_message", 3, "Mensagem de chat"),
]

DEFAULT_TIERS = [
    {
        "slug": "free",
        "name": "Free",
        "credits_per_period": 100,
        "max_upload_mb": 10,
        "max_rows": 50_000,
        "features": ["chat", "overview", "insights"],
        "is_default": True,
    },
    {
        "slug": "pro",
        "name": "Pro",
        "credits_per_period": 2000,
        "max_upload_mb": 50,
        "max_rows": 500_000,
        "features": ["chat", "overview", "insights", "charts"],
        "is_default": False,
    },
    {
        "slug": "internal",
        "name": "Internal",
        "credits_per_period": 999_999,
        "max_upload_mb": 100,
        "max_rows": 1_000_000,
        "features": ["chat", "overview", "insights", "charts"],
        "is_default": False,
    },
]


class Command(BaseCommand):
    help = "Seed tiers and action costs"

    def handle(self, *args, **options):
        for t in DEFAULT_TIERS:
            Tier.objects.update_or_create(slug=t["slug"], defaults=t)
        for action, cost, description in DEFAULT_COSTS:
            ActionCost.objects.update_or_create(
                action=action, defaults={"cost": cost, "description": description}
            )
        self.stdout.write(self.style.SUCCESS("Seed complete"))
