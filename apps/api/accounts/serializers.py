from rest_framework import serializers

from accounts.models import ActionCost, CreditTransaction, User


class UserSerializer(serializers.ModelSerializer):
    credits_balance = serializers.SerializerMethodField()
    tier = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "is_staff",
            "credits_balance",
            "tier",
        )
        read_only_fields = fields

    def get_credits_balance(self, obj: User) -> int:
        account = getattr(obj, "credit_account", None)
        return account.balance if account else 0

    def get_tier(self, obj: User) -> str | None:
        account = getattr(obj, "credit_account", None)
        return account.tier.slug if account else None


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class MagicLinkRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class MagicLinkVerifySerializer(serializers.Serializer):
    token = serializers.CharField()


class GoogleCallbackSerializer(serializers.Serializer):
    code = serializers.CharField()
    state = serializers.CharField()


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = (
            "id",
            "amount",
            "tx_type",
            "action",
            "balance_after",
            "reference_id",
            "created_at",
        )


class ActionCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionCost
        fields = ("action", "cost", "description")
