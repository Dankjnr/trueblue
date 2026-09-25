from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from audit.utils import log_action
from cleaners.models import Cleaner
from common.lockout import clear_attempts, is_locked_out, register_failed_attempt
from customers.models import Customer
from notifications.services import send_sms

from .models import OneTimePasscode, User
from .serializers import (
    ChangePasswordSerializer,
    PasswordLoginSerializer,
    RegisterAccountSerializer,
    RequestOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _user_for_password_login(identifier: str):
    cleaned = (identifier or "").strip()
    if not cleaned:
        return None
    return (
        User.objects.filter(username__iexact=cleaned).first()
        or User.objects.filter(phone_number__iexact=cleaned).first()
    )


class RequestOTPView(APIView):
    """Step 1 of OTP login: issue a one-time code by SMS."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            # Do not reveal whether the number is registered.
            return Response({"detail": "If that number is registered, a code has been sent."})

        if is_locked_out(phone_number):
            return Response(
                {"detail": "Too many attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = OneTimePasscode.issue(user)
        send_sms(user.phone_number, f"Your TrueBlue login code is {otp.code}. It expires in 5 minutes.")
        payload = {"detail": "If that number is registered, a code has been sent."}
        if settings.DEBUG and not settings.SMS_API_KEY:
            payload["debug_code"] = otp.code
        return Response(payload)


class VerifyOTPView(APIView):
    """Step 2 of OTP login: exchange a valid code for JWT tokens."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        requested_role = serializer.validated_data.get("role")

        if is_locked_out(phone_number):
            return Response(
                {"detail": "Too many attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = User.objects.get(phone_number=phone_number)
            otp = user.otps.filter(consumed=False).latest("created_at")
        except (User.DoesNotExist, OneTimePasscode.DoesNotExist):
            register_failed_attempt(phone_number)
            return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

        if requested_role and user.role != requested_role:
            return Response({"detail": "This account is not registered as that role."}, status=status.HTTP_400_BAD_REQUEST)

        if not otp.is_valid(code):
            register_failed_attempt(phone_number)
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        otp.consumed = True
        otp.save(update_fields=["consumed"])
        user.phone_verified = True
        user.last_login = timezone.now()
        user.save(update_fields=["phone_verified", "last_login"])
        clear_attempts(phone_number)
        log_action(user, "login_otp", target=user)

        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class PasswordLoginView(APIView):
    """Password-based login, available as a fallback for customers."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        requested_role = serializer.validated_data.get("role")

        if is_locked_out(identifier):
            return Response(
                {"detail": "Too many attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = _user_for_password_login(identifier)
        if user is None or not user.check_password(password):
            register_failed_attempt(identifier)
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        if requested_role and user.role != requested_role:
            return Response({"detail": "This account is not registered as that role."}, status=status.HTTP_400_BAD_REQUEST)

        clear_attempts(identifier)
        log_action(user, "login_password", target=user)
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class RegisterAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = data.pop("role")
        gender = data.pop("gender", None)
        password = data.pop("password")

        if role == User.Role.ADMIN and not (request.user.is_authenticated and request.user.role == User.Role.ADMIN):
            return Response({"detail": "Only an existing admin can create an admin account."}, status=status.HTTP_403_FORBIDDEN)

        user = User.objects.create_user(
            username=data["username"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone_number=data["phone_number"],
            role=role,
            password=password,
        )
        user.phone_verified = True
        user.save(update_fields=["phone_verified"])

        if role == User.Role.CUSTOMER:
            full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip() or user.username
            Customer.objects.get_or_create(
                user=user,
                defaults={"full_name": full_name, "phone_number": user.phone_number},
            )
        elif role == User.Role.CLEANER:
            Cleaner.objects.get_or_create(
                user=user,
                defaults={"gender": gender or Cleaner.Gender.OTHER},
            )

        log_action(user, "register_account", target=user)
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)}, status=status.HTTP_201_CREATED)


class PromoteAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Only admins can promote users."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get("user_id")
        username = request.data.get("username")
        identifier = user_id if user_id not in (None, "") else username

        if not identifier:
            return Response({"detail": "A user_id or username is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if username is not None and username != "":
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.role = User.Role.ADMIN
        user.save(update_fields=["role"])
        log_action(request.user, "promote_admin", target=user)
        return Response({"detail": "User upgraded to admin.", "user": UserSerializer(user).data})


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(user, "change_password", target=user)
        return Response({"detail": "Password updated."})
