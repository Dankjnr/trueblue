"""
Creates the first admin account from environment variables, if no user
with that username already exists. Safe to run on every deploy (via the
start command) since it's a no-op once the account exists — this exists
specifically for hosts like Render's free tier that don't offer shell
access, so `createsuperuser`'s interactive prompts aren't usable.

Required env vars: ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_PHONE_NUMBER.
If any are unset, the command does nothing (and says so) rather than
failing the deploy.
"""
import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Create the first admin user from ADMIN_USERNAME/ADMIN_PASSWORD/ADMIN_PHONE_NUMBER env vars."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")
        phone_number = os.environ.get("ADMIN_PHONE_NUMBER")

        if not (username and password and phone_number):
            self.stdout.write("ADMIN_USERNAME/ADMIN_PASSWORD/ADMIN_PHONE_NUMBER not fully set — skipping.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"User '{username}' already exists — skipping.")
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            phone_number=phone_number,
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'."))