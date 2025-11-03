from django.urls import path
from . import views

urlpatterns = [
    # Root path - Dashboard/Index page
    path("", views.index, name="index"),
    
    # Telegram webhook endpoint (POST only)
    path("a2a/financeiq/", views.telex_expense_agent, name="telex-expense-agent"),
    
    # Logs endpoint (GET only)
    path("agent-logs/<str:channel_id>.txt", views.telex_logs, name="telex-logs"),
    
    # Additional useful endpoints
    path("api/health/", views.health_check, name="health-check"),
    path("api/expenses/", views.list_expenses, name="list-expenses"),
    path("api/summary/<str:user_id>/", views.get_summary, name="get-summary"),
]