from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import LoginFailure


class Command(BaseCommand):
    help = "Remove expired login-attempt records; schedule daily"

    def handle(self, *args, **options):
        count, _ = LoginFailure.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=1)
        ).delete()
        self.stdout.write(str(count))
