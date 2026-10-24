from django.urls import path

from core.views import (
    AnalysisChartsView,
    AnalysisClaimView,
    AnalysisConversationsView,
    AnalysisDetailView,
    AnalysisInsightsView,
    AnalysisListCreateView,
    ChartsJobView,
    ChatJobView,
    DashboardJobView,
    InsightsJobView,
    OverviewJobView,
    ShareView,
)
from core.views_interest import ProductInterestView
from workers.views import JobDetailView

urlpatterns = [
    path("analyses/", AnalysisListCreateView.as_view()),
    path("analyses/<uuid:pk>/", AnalysisDetailView.as_view()),
    path("analyses/<uuid:pk>/claim/", AnalysisClaimView.as_view()),
    path("analyses/<uuid:pk>/overview/", OverviewJobView.as_view()),
    path("analyses/<uuid:pk>/insights/", InsightsJobView.as_view()),
    path("analyses/<uuid:pk>/charts/", ChartsJobView.as_view()),
    path("analyses/<uuid:pk>/dashboard/", DashboardJobView.as_view()),
    path("analyses/<uuid:pk>/chat/", ChatJobView.as_view()),
    path("analyses/<uuid:pk>/conversations/", AnalysisConversationsView.as_view()),
    path("analyses/<uuid:pk>/insights-list/", AnalysisInsightsView.as_view()),
    path("analyses/<uuid:pk>/charts-list/", AnalysisChartsView.as_view()),
    path("jobs/<uuid:pk>/", JobDetailView.as_view()),
    path("share/<str:token>/", ShareView.as_view()),
    path("interests/", ProductInterestView.as_view()),
]
