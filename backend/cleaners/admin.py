from django.contrib import admin

from .models import BlocklistEntry, Cleaner, Incident


@admin.register(Cleaner)
class CleanerAdmin(admin.ModelAdmin):
    list_display = ["user", "gender", "is_active", "rating", "completed_jobs"]
    list_filter = ["gender", "is_active"]


@admin.register(BlocklistEntry)
class BlocklistEntryAdmin(admin.ModelAdmin):
    list_display = ["cleaner", "customer", "reason", "created_by", "created_at"]
    list_filter = ["reason"]
    readonly_fields = ["created_by", "created_at"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["cleaner", "customer", "severity", "created_at"]
    list_filter = ["severity"]
    readonly_fields = ["recorded_by", "created_at"]
