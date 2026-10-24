from django.urls import path

from accounts.views_auth import (
    AuthMethodsView,
    GoogleCallbackView,
    GoogleStartView,
    LogoutView,
    MagicLinkRequestView,
    MagicLinkVerifyView,
    MeView,
    RefreshView,
)

urlpatterns = [
    path("methods/", AuthMethodsView.as_view()),
    path("magic-link/", MagicLinkRequestView.as_view()),
    path("magic-link/verify/", MagicLinkVerifyView.as_view()),
    path("google/start/", GoogleStartView.as_view()),
    path("google/callback/", GoogleCallbackView.as_view()),
    path("token/refresh/", RefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
]
