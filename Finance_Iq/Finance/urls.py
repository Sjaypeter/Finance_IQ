from django.urls import path
from .views import telex_expense_agent, telex_logs

urlpatterns = [
    path("a2a/financeiq/", telex_expense_agent, name="telex-expense-agent"),
    path("agent-logs/<str:channel_id>.txt", telex_logs, name="telex-logs"),
]