from django.contrib import admin

from accounts.models import (
    ActionCost,
    CreditAccount,
    CreditTransaction,
    MagicLinkToken,
    SocialAccount,
    Tier,
    User,
)
from accounts.services.credits import adjust_balance


class CreditAccountInline(admin.StackedInline):
    model = CreditAccount
    extra = 0


class SocialAccountInline(admin.TabularInline):
    model = SocialAccount
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    search_fields = ("email",)
    list_filter = ("is_staff", "is_active")
    inlines = [CreditAccountInline, SocialAccountInline]
    actions = ["adjust_plus_100"]

    @admin.action(description="Ajustar +100 créditos")
    def adjust_plus_100(self, request, queryset):
        for user in queryset:
            adjust_balance(user, delta=100, meta={"admin": request.user.email})


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "credits_per_period",
        "max_upload_mb",
        "max_rows",
        "is_default",
    )


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "tx_type", "action", "amount", "balance_after", "created_at")
    list_filter = ("tx_type", "action")
    search_fields = ("user__email", "reference_id")
    readonly_fields = [f.name for f in CreditTransaction._meta.fields]


@admin.register(ActionCost)
class ActionCostAdmin(admin.ModelAdmin):
    list_display = ("action", "cost", "description")


@admin.register(MagicLinkToken)
class MagicLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "expires_at", "used_at")
    search_fields = ("email",)


@admin.register(CreditAccount)
class CreditAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "tier", "balance", "updated_at")
    search_fields = ("user__email",)
