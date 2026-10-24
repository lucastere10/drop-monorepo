from __future__ import annotations

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services.admin_ops import (
    AdminOpsError,
    adjust_user_credits,
    list_analyses,
    list_users,
    overview,
    parse_limit,
    update_user,
)


class AdminAPIView(APIView):
    permission_classes = [IsAdminUser]

    def permission_denied(self, request, message=None, code=None):
        raise PermissionDenied(detail="Acesso restrito a operadores.")

    def handle_ops(self, exc: AdminOpsError) -> Response:
        return Response(
            {"code": exc.code, "message": exc.message, "details": {}},
            status=exc.status,
        )


class AdminUserPatchSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False)
    tier = serializers.SlugField(required=False)
    is_staff = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Nada para atualizar.")
        return attrs


class AdminCreditAdjustSerializer(serializers.Serializer):
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=255, trim_whitespace=True)

    def validate_delta(self, value: int) -> int:
        if value == 0:
            raise serializers.ValidationError("O delta não pode ser zero.")
        return value

    def validate_reason(self, value: str) -> str:
        if not value:
            raise serializers.ValidationError("Informe o motivo.")
        return value


def _invalid(ser: serializers.Serializer) -> Response:
    message = "Dados inválidos."
    errors = ser.errors
    for value in errors.values():
        if isinstance(value, list) and value:
            message = str(value[0])
            break
        if isinstance(value, str):
            message = value
            break
    return Response(
        {"code": "invalid", "message": message, "details": errors},
        status=400,
    )


class OverviewView(AdminAPIView):
    def get(self, request):
        return Response(overview())


class UsersView(AdminAPIView):
    def get(self, request):
        limit = parse_limit(request.query_params.get("limit"))
        return Response(list_users(limit=limit))


class UserDetailView(AdminAPIView):
    def patch(self, request, user_id):
        ser = AdminUserPatchSerializer(data=request.data)
        if not ser.is_valid():
            return _invalid(ser)
        data = ser.validated_data
        try:
            payload = update_user(
                request.user,
                user_id,
                is_active=data.get("is_active"),
                tier_slug=data.get("tier"),
                is_staff=data.get("is_staff"),
            )
        except AdminOpsError as exc:
            return self.handle_ops(exc)
        return Response(payload)


class UserCreditsView(AdminAPIView):
    def post(self, request, user_id):
        ser = AdminCreditAdjustSerializer(data=request.data)
        if not ser.is_valid():
            return _invalid(ser)
        try:
            payload = adjust_user_credits(
                request.user,
                user_id,
                delta=ser.validated_data["delta"],
                reason=ser.validated_data["reason"],
            )
        except AdminOpsError as exc:
            return self.handle_ops(exc)
        return Response(payload)


class AnalysesView(AdminAPIView):
    def get(self, request):
        limit = parse_limit(request.query_params.get("limit"))
        return Response(list_analyses(limit=limit))
