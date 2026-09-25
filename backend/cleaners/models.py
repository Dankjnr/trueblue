from django.conf import settings
from django.db import models


class Cleaner(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cleaner_profile")
    gender = models.CharField(max_length=10, choices=Gender.choices)
    home_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    home_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Inactive cleaners are never recommended.")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    completed_jobs = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class BlocklistEntry(models.Model):
    """A cleaner who must never be recommended/assigned to a given customer."""

    class Reason(models.TextChoices):
        GENDER_MISMATCH = "gender_mismatch", "Gender preference mismatch"
        PAST_INCIDENT = "past_incident", "Past incident"
        INFRACTION = "infraction", "Infraction"
        MANUAL = "manual", "Manually blocked by admin"

    cleaner = models.ForeignKey(Cleaner, on_delete=models.CASCADE, related_name="blocklist_entries")
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="blocked_cleaners")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cleaner", "customer")

    def __str__(self):
        return f"{self.cleaner} blocked for {self.customer} ({self.reason})"


class Incident(models.Model):
    """A logged incident or infraction against a cleaner, feeding both the
    blocklist and future ranking decisions."""

    class Severity(models.TextChoices):
        MINOR = "minor", "Minor"
        MAJOR = "major", "Major"

    cleaner = models.ForeignKey(Cleaner, on_delete=models.CASCADE, related_name="incidents")
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    severity = models.CharField(max_length=10, choices=Severity.choices)
    description = models.TextField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
