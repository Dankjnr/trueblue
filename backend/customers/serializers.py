from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Customer._meta.get_field("user").remote_field.model.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            "id", "user", "full_name", "phone_number", "default_address",
            "notes", "created_by_admin", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by_admin", "created_at", "updated_at"]


class CustomerPublicSerializer(serializers.ModelSerializer):
    """What a customer sees of their own profile — no internal notes."""

    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone_number", "default_address"]
