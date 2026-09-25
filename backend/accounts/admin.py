from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "first_name", "last_name", "role", "phone_number", "is_active"]
    list_filter = ["role", "is_active"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("TrueBlue", {"fields": ("role", "phone_number", "phone_verified")}),
    )
