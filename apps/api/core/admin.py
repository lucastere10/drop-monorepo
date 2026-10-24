from django.contrib import admin

from core.models import (
    Analysis,
    ChartSpec,
    Conversation,
    Insight,
    Message,
    ProductInterest,
    UploadedFile,
)


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "user", "size_bytes", "status", "created_at")
    search_fields = ("original_name", "user__email")


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "n_rows", "n_cols", "quality_score", "created_at")
    search_fields = ("title", "user__email")


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Insight)
admin.site.register(ChartSpec)


@admin.register(ProductInterest)
class ProductInterestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email")
    readonly_fields = ("created_at",)
