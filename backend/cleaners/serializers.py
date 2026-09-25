from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import BlocklistEntry, Cleaner, Incident


class CleanerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Cleaner
        fields = [
            "id", "user", "gender", "home_latitude", "home_longitude",
            "is_active", "rating", "completed_jobs", "created_at",
        ]
        read_only_fields = ["id", "rating", "completed_jobs", "created_at"]


class BlocklistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlocklistEntry
        fields = ["id", "cleaner", "customer", "reason", "note", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ["id", "cleaner", "customer", "severity", "description", "recorded_by", "created_at"]
        read_only_fields = ["id", "recorded_by", "created_at"]
