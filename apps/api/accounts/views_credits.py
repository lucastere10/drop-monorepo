from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ActionCost, CreditTransaction
from accounts.serializers import ActionCostSerializer, CreditTransactionSerializer, UserSerializer


class CreditsMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_data = UserSerializer(request.user).data
        account = request.user.credit_account
        return Response(
            {
                "balance": account.balance,
                "tier": {
                    "slug": account.tier.slug,
                    "name": account.tier.name,
                    "max_upload_mb": account.tier.max_upload_mb,
                    "max_rows": account.tier.max_rows,
                    "features": account.tier.features,
                },
                "user": user_data,
            }
        )


class CreditsTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CreditTransaction.objects.filter(user=request.user).order_by("-created_at")[:100]
        return Response(CreditTransactionSerializer(qs, many=True).data)


class CreditsCostsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ActionCost.objects.all().order_by("action")
        return Response(ActionCostSerializer(qs, many=True).data)
