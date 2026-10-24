from rest_framework import serializers

from core.models import Analysis, ChartSpec, Conversation, Insight, Message
from core.services.dashboard_layout import validate_dashboard_layout


class AnalysisSerializer(serializers.ModelSerializer):
    is_anonymous = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = (
            "id",
            "title",
            "summary",
            "n_rows",
            "n_cols",
            "quality_score",
            "quality_grade",
            "is_favorite",
            "is_public",
            "share_token",
            "overview_text",
            "overview_job_id",
            "dashboard_layout",
            "dashboard_job_id",
            "expires_at",
            "is_anonymous",
            "is_expired",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "summary",
            "n_rows",
            "n_cols",
            "quality_score",
            "quality_grade",
            "share_token",
            "overview_text",
            "overview_job_id",
            "dashboard_job_id",
            "expires_at",
            "is_anonymous",
            "is_expired",
            "created_at",
            "updated_at",
        )

    def validate_dashboard_layout(self, value):
        if self.instance is None:
            return value or {}
        return validate_dashboard_layout(value, self.instance)

    def get_is_anonymous(self, obj: Analysis) -> bool:
        return obj.is_anonymous

    def get_is_expired(self, obj: Analysis) -> bool:
        return obj.is_expired


class AnalysisListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = (
            "id",
            "title",
            "n_rows",
            "n_cols",
            "quality_score",
            "quality_grade",
            "is_favorite",
            "created_at",
        )


class MessageSerializer(serializers.ModelSerializer):
    charts = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id", "role", "content", "meta", "charts", "created_at")

    def get_charts(self, obj: Message):
        ids = (obj.meta or {}).get("chart_ids") or []
        if not ids:
            return []
        qs = ChartSpec.objects.filter(id__in=ids)
        by_id = {str(c.id): c for c in qs}
        ordered = [by_id[str(i)] for i in ids if str(i) in by_id]
        return ChartSpecSerializer(ordered, many=True).data


class ConversationSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "created_at", "messages")

    def get_messages(self, obj: Conversation):
        qs = obj.messages.order_by("created_at")
        return MessageSerializer(qs, many=True).data


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = ("id", "kind", "content", "meta", "created_at")


INTEREST_SLUGS = ("charts", "insights", "chat", "ml")


class ProductInterestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    email = serializers.EmailField()
    interests = serializers.ListField(
        child=serializers.ChoiceField(choices=INTEREST_SLUGS),
        allow_empty=False,
    )
    comment = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    analysis_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_name(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Informe seu nome.")
        return value

    def validate_interests(self, value: list[str]) -> list[str]:
        unique: list[str] = []
        for item in value:
            if item not in unique:
                unique.append(item)
        return unique


class ChartSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartSpec
        fields = ("id", "title", "chart_type", "spec", "created_at")
