import random
import string

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CLEANER = "cleaner", "Cleaner"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(max_length=10, choices=Role.choices)
    phone_number = models.CharField(max_length=20, unique=True)
    phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone_number"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class OneTimePasscode(models.Model):
    """
    Short-lived OTP used for cleaner/admin login instead of (or in addition
    to) a password, per the security requirement for OTP-based login where
    feasible.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)

    @classmethod
    def issue(cls, user, ttl_seconds=300):
        code = "".join(random.choices(string.digits, k=6))
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )

    def is_valid(self, code: str) -> bool:
        return (
            not self.consumed
            and self.code == code
            and timezone.now() <= self.expires_at
        )
