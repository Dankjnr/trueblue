from django.conf import settings
from django.db import models
from django.utils import timezone

from common.encryption import EncryptedTextField


class Job(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SHORTLISTED = "shortlisted", "Shortlisted"
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    class GenderPreference(models.TextChoices):
        ANY = "any", "No preference"
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    # --- intake -------------------------------------------------------
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="jobs")
    location_summary = models.CharField(max_length=255, help_text="e.g. '14 Okpanam Road, Asaba'")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    cleaners_needed = models.PositiveSmallIntegerField(default=1)
    gender_preference = models.CharField(max_length=10, choices=GenderPreference.choices, default=GenderPreference.ANY)
    requested_date = models.DateField()
    requires_access_code = models.BooleanField(default=False)
    access_code_location = models.CharField(
        max_length=100, blank=True, help_text="Where the code applies, e.g. 'estate gate', 'house gate'."
    )
    access_code = EncryptedTextField(blank=True, help_text="Encrypted at rest; only decrypted for authorized reads.")
    intake_channel = models.CharField(
        max_length=10,
        choices=[("app", "App"), ("phone", "Phone-in")],
        default="app",
    )
    taken_by_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        help_text="Admin who logged a phone-in request, if applicable.",
    )

    # --- lifecycle ------------------------------------------------------
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- post-acceptance job packet -------------------------------------
    start_time = models.TimeField(null=True, blank=True)
    timeframe_minutes = models.PositiveIntegerField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    packet_sent_at = models.DateTimeField(null=True, blank=True)

    # --- decision trail --------------------------------------------------
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["requested_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "requested_date"]),
        ]

    def __str__(self):
        return f"Job #{self.id} — {self.location_summary} ({self.requested_date})"

    @property
    def urgency(self) -> str:
        """
        red = 2+ days away, orange = tomorrow, green = today.
        Only meaningful while the job hasn't been resolved yet.
        """
        days_out = (self.requested_date - timezone.localdate()).days
        if days_out <= 0:
            return "green"
        if days_out == 1:
            return "orange"
        return "red"

    def access_code_visible_to(self, user) -> bool:
        """
        Access codes are only visible to the assigned cleaner once the job
        is accepted, and hidden again after completion. Admins can always
        view them (and doing so is audit-logged by the view layer).
        """
        if user.role == "admin":
            return True
        if user.role != "cleaner":
            return False
        assignment = self.assignments.filter(cleaner__user=user, status=JobAssignment.Status.ACCEPTED).first()
        if not assignment:
            return False
        return self.status in (Job.Status.ACCEPTED, Job.Status.IN_PROGRESS)


class JobAssignment(models.Model):
    """
    One row per cleaner considered/assigned for a job. Supports the
    'admin reviews a shortlist, picks one (or reassigns after a decline)'
    flow, and keeps the full offer history rather than overwriting it.
    """
    class Status(models.TextChoices):
        RECOMMENDED = "recommended", "Recommended"
        OFFERED = "offered", "Offered"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        TIMED_OUT = "timed_out", "Timed out"
        WITHDRAWN = "withdrawn", "Withdrawn"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="assignments")
    cleaner = models.ForeignKey("cleaners.Cleaner", on_delete=models.PROTECT, related_name="assignments")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.RECOMMENDED)
    rank_score = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    rank_breakdown = models.JSONField(default=dict, blank=True)
    offered_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "cleaner")
        ordering = ["-rank_score"]


class StatusChange(models.Model):
    """Full audit trail of job status transitions, independent of the
    general AuditLog, for quick per-job history display in the UI."""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=15, blank=True)
    to_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
