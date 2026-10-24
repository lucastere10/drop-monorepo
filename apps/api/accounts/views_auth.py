from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.serializers import (
    GoogleCallbackSerializer,
    MagicLinkRequestSerializer,
    MagicLinkVerifySerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from accounts.services import auth as auth_services


class AuthMethodsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"methods": auth_services.available_auth_methods()})


class MagicLinkRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = MagicLinkRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            link = auth_services.request_magic_link(ser.validated_data["email"], request=request)
        except auth_services.AuthError as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_429_TOO_MANY_REQUESTS
                if exc.code == "rate_limited"
                else status.HTTP_400_BAD_REQUEST,
            )
        if getattr(settings, "DROP_ENV", "local") == "local":
            return Response({"dev_verify_url": link})
        return Response(status=status.HTTP_204_NO_CONTENT)


class MagicLinkVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = MagicLinkVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            tokens = auth_services.verify_magic_link(ser.validated_data["token"])
        except auth_services.AuthError as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(tokens)


class GoogleStartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            data = auth_services.google_start()
        except auth_services.AuthError as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(data)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = GoogleCallbackSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            tokens = auth_services.google_callback(
                code=ser.validated_data["code"], state=ser.validated_data["state"]
            )
        except auth_services.AuthError as exc:
            return Response(
                {"code": exc.code, "message": exc.message, "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:  # noqa: BLE001
            return Response(
                {"code": "oauth_failed", "message": "Falha no login Google.", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(tokens)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        ser = UserUpdateSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:  # noqa: BLE001
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
