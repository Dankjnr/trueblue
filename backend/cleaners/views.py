from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.utils import log_action
from common.permissions import IsAdmin

from .models import BlocklistEntry, Cleaner, Incident
from .serializers import BlocklistEntrySerializer, CleanerSerializer, IncidentSerializer


class CleanerViewSet(viewsets.ModelViewSet):
    queryset = Cleaner.objects.select_related("user").all().order_by("user__first_name")
    serializer_class = CleanerSerializer

    def get_permissions(self):
        if self.action in ("list", "create", "destroy"):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return super().get_queryset()
        if user.role == "cleaner":
            return super().get_queryset().filter(user=user)
        return super().get_queryset().none()

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, "update_cleaner", target=instance)


class BlocklistEntryViewSet(viewsets.ModelViewSet):
    """Admin-only — who is blocked from working for which customer, and why."""
    queryset = BlocklistEntry.objects.select_related("cleaner__user", "customer").all()
    serializer_class = BlocklistEntrySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["cleaner", "customer", "reason"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        log_action(self.request.user, "block_cleaner", target=instance, metadata={
            "cleaner_id": instance.cleaner_id, "customer_id": instance.customer_id, "reason": instance.reason,
        })

    def perform_destroy(self, instance):
        log_action(self.request.user, "unblock_cleaner", target=instance, metadata={
            "cleaner_id": instance.cleaner_id, "customer_id": instance.customer_id,
        })
        instance.delete()


class IncidentViewSet(viewsets.ModelViewSet):
    """Admin-only — the incident log behind blocklist decisions and future ranking."""
    queryset = Incident.objects.select_related("cleaner__user", "customer").all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["cleaner", "severity"]

    def perform_create(self, serializer):
        instance = serializer.save(recorded_by=self.request.user)
        log_action(self.request.user, "record_incident", target=instance)
