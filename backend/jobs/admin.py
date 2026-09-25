from django.contrib import admin

from .models import Job, JobAssignment, StatusChange


class JobAssignmentInline(admin.TabularInline):
    model = JobAssignment
    extra = 0
    readonly_fields = ["rank_score", "rank_breakdown", "offered_at", "responded_at", "created_at"]


class StatusChangeInline(admin.TabularInline):
    model = StatusChange
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "note", "created_at"]
    can_delete = False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "location_summary", "requested_date", "status", "urgency"]
    list_filter = ["status", "gender_preference", "intake_channel"]
    search_fields = ["location_summary", "customer__full_name"]
    inlines = [JobAssignmentInline, StatusChangeInline]
    readonly_fields = ["created_at", "updated_at", "packet_sent_at", "responded_at", "completed_at"]

    def urgency(self, obj):
        return obj.urgency
