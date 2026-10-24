from django.urls import path

from accounts.views_credits import CreditsCostsView, CreditsMeView, CreditsTransactionsView

urlpatterns = [
    path("me/", CreditsMeView.as_view()),
    path("transactions/", CreditsTransactionsView.as_view()),
    path("costs/", CreditsCostsView.as_view()),
]
