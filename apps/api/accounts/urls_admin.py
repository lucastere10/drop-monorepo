from django.urls import path

from accounts.views_admin import (
    AnalysesView,
    OverviewView,
    UserCreditsView,
    UserDetailView,
    UsersView,
)

urlpatterns = [
    path("overview/", OverviewView.as_view()),
    path("users/", UsersView.as_view()),
    path("users/<uuid:user_id>/", UserDetailView.as_view()),
    path("users/<uuid:user_id>/credits/", UserCreditsView.as_view()),
    path("analyses/", AnalysesView.as_view()),
]
