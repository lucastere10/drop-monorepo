from __future__ import annotations

from django.core.management.base import BaseCommand

from core.services.cleanup import cleanup_expired_uploads


class Command(BaseCommand):
    help = "Delete expired anonymous analyses and old upload files"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        deleted = cleanup_expired_uploads(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"Cleaned {deleted} records/files"))
