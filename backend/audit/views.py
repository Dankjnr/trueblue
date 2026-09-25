from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets

from common.permissions import IsAdmin

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.get_full_name", default="", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor", "actor_name", "action", "target_type", "target_id",
            "metadata", "ip_address", "created_at",
        ]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — admins can view the trail but never edit or delete it."""
    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["action", "target_type", "actor"]
