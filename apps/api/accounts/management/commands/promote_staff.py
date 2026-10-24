from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Mark an existing passwordless user as staff"

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        email = options["email"].strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError(f"User not found: {email}") from exc
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self.stdout.write(self.style.SUCCESS(f"{user.email} is staff"))
