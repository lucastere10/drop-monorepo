from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ProductInterest
from core.serializers import ProductInterestSerializer
from core.services.limits import RateLimited, check_interest


class ProductInterestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ProductInterestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {
                    "code": "invalid",
                    "message": "Confira nome, e-mail e o que você quer usar.",
                    "details": ser.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            check_interest(request)
        except RateLimited as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        data = ser.validated_data
        interest = ProductInterest.objects.create(
            name=data["name"],
            email=data["email"],
            interests=data["interests"],
            comment=data.get("comment") or "",
            analysis_id=data.get("analysis_id"),
        )
        return Response({"id": str(interest.id)}, status=status.HTTP_201_CREATED)
