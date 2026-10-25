import os
from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from core.models import Branch, User


class Command(BaseCommand):
    help = "Create the first manager; no public staff registration exists"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="owner")
        parser.add_argument("--branch", default="Magribi · Ақсай")

    def handle(self, *args, **opts):
        if User.objects.filter(role="manager").exists():
            raise CommandError("A manager already exists; use the manager interface")
        password = os.getenv("BOOTSTRAP_PASSWORD") or getpass(
            "Manager password (10+ characters): "
        )
        validate_password(password, User(username=opts["username"]))
        with transaction.atomic():
            branch = Branch.objects.create(name=opts["branch"])
            User.objects.create_user(
                username=opts["username"].lower(),
                password=password,
                first_name="Басқарушы",
                role="manager",
                branch=branch,
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Manager created. Sign in at /manager. Password is not printed or stored in source."
            )
        )
