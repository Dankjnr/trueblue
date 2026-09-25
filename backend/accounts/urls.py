from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    MeView,
    PasswordLoginView,
    PromoteAdminView,
    RegisterAccountView,
    RequestOTPView,
    VerifyOTPView,
)

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view(), name="otp-request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("login/", PasswordLoginView.as_view(), name="password-login"),
    path("register/", RegisterAccountView.as_view(), name="register-account"),
    path("promote-admin/", PromoteAdminView.as_view(), name="promote-admin"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
