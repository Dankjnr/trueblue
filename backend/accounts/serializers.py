from django.contrib.auth import password_validation
from rest_framework import serializers

from cleaners.models import Cleaner

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "phone_number", "role", "phone_verified"]
        read_only_fields = ["id", "role", "phone_verified"]


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)
    role = serializers.ChoiceField(
        choices=[User.Role.ADMIN, User.Role.CUSTOMER, User.Role.CLEANER],
        required=False,
        allow_null=True,
    )


class PasswordLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[User.Role.ADMIN, User.Role.CUSTOMER, User.Role.CLEANER],
        required=False,
        allow_null=True,
    )


class RegisterAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[User.Role.ADMIN, User.Role.CUSTOMER, User.Role.CLEANER])
    gender = serializers.ChoiceField(choices=Cleaner.Gender.choices, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone_number", "password", "role", "gender"]

    def validate(self, attrs):
        role = attrs.get("role")
        if role == User.Role.CLEANER and not attrs.get("gender"):
            raise serializers.ValidationError({"gender": "Cleaner accounts must include a gender."})
        if role == User.Role.CUSTOMER and attrs.get("gender"):
            attrs.pop("gender")
        if User.objects.filter(phone_number=attrs["phone_number"]).exists():
            raise serializers.ValidationError({"phone_number": "An account already exists with that phone number."})
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "That username is already taken."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop("role")
        password = validated_data.pop("password")
        gender = validated_data.pop("gender", None)
        user = User.objects.create_user(role=role, password=password, **validated_data)
        user.phone_verified = True
        user.save(update_fields=["phone_verified"])
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
