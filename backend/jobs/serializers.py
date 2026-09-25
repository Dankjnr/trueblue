from rest_framework import serializers

from cleaners.serializers import CleanerSerializer
from customers.serializers import CustomerSerializer

from .models import Job, JobAssignment, StatusChange


class JobAssignmentSerializer(serializers.ModelSerializer):
    cleaner = CleanerSerializer(read_only=True)

    class Meta:
        model = JobAssignment
        fields = [
            "id", "job", "cleaner", "status", "rank_score", "rank_breakdown",
            "offered_at", "responded_at", "created_at",
        ]
        read_only_fields = fields


class StatusChangeSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", default="", read_only=True)

    class Meta:
        model = StatusChange
        fields = ["id", "from_status", "to_status", "changed_by", "changed_by_name", "note", "created_at"]
        read_only_fields = fields


class JobCreateSerializer(serializers.ModelSerializer):
    """Used for request intake — both self-service and admin phone-in."""

    customer = serializers.PrimaryKeyRelatedField(read_only=False, required=False, allow_null=True, queryset=Job._meta.get_field("customer").remote_field.model.objects.all())

    class Meta:
        model = Job
        fields = [
            "id", "customer", "location_summary", "latitude", "longitude",
            "cleaners_needed", "gender_preference", "requested_date",
            "requires_access_code", "access_code_location", "access_code",
            "intake_channel",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        requires_access_code = attrs.get("requires_access_code")
        if requires_access_code:
            if not attrs.get("access_code_location"):
                raise serializers.ValidationError(
                    {"access_code_location": "Say where the access code applies (e.g. estate gate, house gate)."}
                )
            if not attrs.get("access_code"):
                raise serializers.ValidationError({"access_code": "Access code is required when one is needed."})
        else:
            attrs["access_code_location"] = ""
            attrs["access_code"] = ""
        return attrs


class JobDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    urgency = serializers.CharField(read_only=True)
    assignments = JobAssignmentSerializer(many=True, read_only=True)
    status_history = StatusChangeSerializer(many=True, read_only=True)
    access_code = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "customer", "location_summary", "latitude", "longitude",
            "cleaners_needed", "gender_preference", "requested_date", "urgency",
            "requires_access_code", "access_code_location", "access_code",
            "intake_channel", "status", "start_time", "timeframe_minutes",
            "special_instructions", "packet_sent_at", "assignments",
            "status_history", "created_at", "updated_at", "completed_at",
        ]
        read_only_fields = [f for f in fields if f != "special_instructions"]

    def get_access_code(self, obj: Job):
        request = self.context.get("request")
        if request is None or not obj.access_code_visible_to(request.user):
            return None
        return obj.access_code


class JobListSerializer(serializers.ModelSerializer):
    """Lean representation for the admin dashboard list/grid."""
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    urgency = serializers.CharField(read_only=True)
    assigned_cleaner = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "customer_name", "location_summary", "cleaners_needed",
            "gender_preference", "requested_date", "urgency", "status",
            "assigned_cleaner", "created_at",
        ]

    def get_assigned_cleaner(self, obj: Job):
        assignment = obj.assignments.filter(
            status__in=[JobAssignment.Status.OFFERED, JobAssignment.Status.ACCEPTED]
        ).order_by("-created_at").first()
        if not assignment:
            return None
        return {
            "id": assignment.cleaner_id,
            "name": assignment.cleaner.user.get_full_name(),
            "status": assignment.status,
        }


class AssignCleanerSerializer(serializers.Serializer):
    cleaner_id = serializers.IntegerField()


class RespondToOfferSerializer(serializers.Serializer):
    accept = serializers.BooleanField()


class JobPacketSerializer(serializers.Serializer):
    """The detail packet an admin fills in once a cleaner accepts."""
    customer_phone_override = serializers.CharField(required=False, allow_blank=True)
    access_code = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.TimeField()
    timeframe_minutes = serializers.IntegerField(min_value=15)
    special_instructions = serializers.CharField(required=False, allow_blank=True)
