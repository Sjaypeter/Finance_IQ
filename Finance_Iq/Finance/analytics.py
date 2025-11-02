from django.db.models import Sum
from datetime import date, timedelta
from .models import Expense


def get_weekly_summary(user_id):
    start = date.today() - timedelta(days=7)
    expenses = Expense.objects.filter(user_id=user_id, date_gte=start)
    total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    by_category = expenses.values("category").annotate(total=Sum("amount")).order_by("-total")

    summary_lines = [f"💰 Total spent this week: ₦{total:,.2f}"]
    for c in by_category:
        summary_lines.append(f"• {c['category'].capitalize()}: ₦{c['total']:,.2f}")
    return "\n".join(summary_lines)