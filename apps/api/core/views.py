from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Analysis, ChartSpec, Conversation, Insight
from core.serializers import (
    AnalysisListSerializer,
    AnalysisSerializer,
    ChartSpecSerializer,
    ConversationSerializer,
    InsightSerializer,
)
from core.services.claim import ClaimError, claim_anonymous_analysis
from core.services.limits import RateLimited, check_ai_jobs, check_upload
from core.services.pipeline import IngestError, create_analysis_from_upload
from workers.services.dispatch import enqueue_job


def _can_read_analysis(request, analysis: Analysis) -> bool:
    if analysis.is_expired:
        return False
    if analysis.user_id is None:
        return True
    if analysis.is_public:
        return True
    return request.user.is_authenticated and request.user.id == analysis.user_id


def _owned_analysis(request, pk) -> Analysis | None:
    if not request.user.is_authenticated:
        return None
    return Analysis.objects.filter(user=request.user, pk=pk).first()


def _owned_or_claim(request, pk) -> Analysis | None:
    """Return owned analysis, claiming an anonymous one when the user is authenticated."""
    owned = _owned_analysis(request, pk)
    if owned:
        return owned
    if not request.user.is_authenticated:
        return None
    anon = Analysis.objects.filter(pk=pk, user__isnull=True).first()
    if not anon:
        return None
    try:
        return claim_anonymous_analysis(user=request.user, analysis=anon)
    except ClaimError:
        return None


class AnalysisListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        qs = Analysis.objects.filter(user=request.user).order_by("-created_at")
        return Response(AnalysisListSerializer(qs, many=True).data)

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response(
                {"code": "missing_file", "message": "Campo file é obrigatório.", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user if request.user.is_authenticated else None
        try:
            check_upload(request)
        except RateLimited as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            analysis = create_analysis_from_upload(user=user, uploaded=uploaded)
        except IngestError as exc:
            http_status = (
                status.HTTP_402_PAYMENT_REQUIRED
                if exc.code == "insufficient_credits"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                {"code": exc.code, "message": exc.message, "details": exc.details},
                status=http_status,
            )
        return Response(AnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


class AnalysisDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        obj = Analysis.objects.filter(pk=pk).first()
        if not obj or not _can_read_analysis(request, obj):
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(AnalysisSerializer(obj).data)

    def patch(self, request, pk):
        if not request.user.is_authenticated:
            return Response(
                {"code": "auth_required", "message": "Faça login para editar.", "details": {}},
                status=401,
            )
        obj = _owned_analysis(request, pk)
        if not obj:
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        ser = AnalysisSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        if obj.is_public:
            obj.ensure_share_token()
        return Response(AnalysisSerializer(obj).data)

    def delete(self, request, pk):
        if not request.user.is_authenticated:
            return Response(
                {"code": "auth_required", "message": "Faça login para excluir.", "details": {}},
                status=401,
            )
        obj = _owned_analysis(request, pk)
        if not obj:
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnalysisClaimView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        analysis = Analysis.objects.filter(pk=pk).first()
        if not analysis:
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            claimed = claim_anonymous_analysis(user=request.user, analysis=analysis)
        except ClaimError as exc:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if exc.code == "not_found"
                else status.HTTP_409_CONFLICT
                if exc.code == "already_owned"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status_code,
            )
        return Response(AnalysisSerializer(claimed).data)


class AnalysisActionJobView(APIView):
    permission_classes = [IsAuthenticated]
    job_type: str = ""
    credit_action: str = ""

    def post(self, request, pk):
        analysis = _owned_or_claim(request, pk)
        if not analysis:
            anon = Analysis.objects.filter(pk=pk, user__isnull=True).first()
            if anon and not anon.is_expired:
                return Response(
                    {
                        "code": "auth_required",
                        "message": "Faça login para usar chat, insights e gráficos IA.",
                        "details": {},
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            check_ai_jobs(request.user)
        except RateLimited as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        payload = {
            "analysis_id": str(analysis.id),
            **(request.data if isinstance(request.data, dict) else {}),
        }
        try:
            job = enqueue_job(
                user=request.user,
                job_type=self.job_type,
                payload=payload,
                credit_action=self.credit_action,
                analysis=analysis,
            )
        except Exception as exc:
            from accounts.services.credits import InsufficientCredits

            if isinstance(exc, InsufficientCredits):
                details = {}
                if exc.required is not None and exc.balance is not None:
                    details = {"required": exc.required, "balance": exc.balance}
                return Response(
                    {"code": "insufficient_credits", "message": str(exc), "details": details},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
            raise
        return Response({"job_id": str(job.id), "status": job.status}, status=status.HTTP_202_ACCEPTED)


class OverviewJobView(AnalysisActionJobView):
    job_type = "ai_overview"
    credit_action = "ai.overview"


class InsightsJobView(AnalysisActionJobView):
    job_type = "ai_insights"
    credit_action = "ai.insights"


class ChartsJobView(AnalysisActionJobView):
    job_type = "ai_charts"
    credit_action = "ai.chart"


class DashboardJobView(AnalysisActionJobView):
    job_type = "ai_dashboard"
    credit_action = "ai.dashboard"

    def post(self, request, pk):
        return Response(
            {
                "code": "gone",
                "message": "O quadro de gráficos é montado na abertura da análise.",
                "details": {},
            },
            status=status.HTTP_410_GONE,
        )


class ChatJobView(AnalysisActionJobView):
    job_type = "ai_chat"
    credit_action = "ai.chat_message"


class AnalysisConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = _owned_or_claim(request, pk)
        if not analysis:
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=404,
            )
        qs = (
            Conversation.objects.filter(analysis=analysis)
            .prefetch_related("messages")
            .order_by("created_at")
        )
        return Response(ConversationSerializer(qs, many=True).data)


class AnalysisInsightsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        analysis = Analysis.objects.filter(pk=pk).first()
        if not analysis or not _can_read_analysis(request, analysis):
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=404,
            )
        qs = Insight.objects.filter(analysis=analysis).order_by("-created_at")
        return Response(InsightSerializer(qs, many=True).data)


class AnalysisChartsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        analysis = Analysis.objects.filter(pk=pk).first()
        if not analysis or not _can_read_analysis(request, analysis):
            return Response(
                {"code": "not_found", "message": "Análise não encontrada.", "details": {}},
                status=404,
            )
        qs = ChartSpec.objects.filter(analysis=analysis).order_by("-created_at")
        return Response(ChartSpecSerializer(qs, many=True).data)


class ShareView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        analysis = Analysis.objects.filter(share_token=token, is_public=True).first()
        if not analysis or analysis.is_expired:
            return Response(
                {"code": "not_found", "message": "Compartilhamento não encontrado.", "details": {}},
                status=404,
            )
        data = AnalysisSerializer(analysis).data
        data["insights"] = InsightSerializer(
            Insight.objects.filter(analysis=analysis), many=True
        ).data
        data["charts"] = ChartSpecSerializer(
            ChartSpec.objects.filter(analysis=analysis), many=True
        ).data
        return Response(data)
