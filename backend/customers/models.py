from django.conf import settings
from django.db import models


class Customer(models.Model):
    """
    Extends a User(role=customer) with profile data. Also supports
    phone-in customers who never create an account — an admin can create
    a Customer with `user=None` and just the contact details, per the
    'admin entering a phone-in request' workflow.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="customer_profile"
    )
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    default_address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes visible to admins only.")
    created_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["phone_number"])]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"
