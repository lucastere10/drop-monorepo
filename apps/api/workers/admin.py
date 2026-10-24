from django.contrib import admin

from workers.models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "job_type", "status", "user", "created_at")
    list_filter = ("status", "job_type")
    search_fields = ("id", "user__email")
