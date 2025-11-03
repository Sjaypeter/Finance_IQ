import json
import logging
from datetime import date, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import Expense
from .parser import parse_expense
from .analytics import get_weekly_summary

# Configure logging with rotation
logger = logging.getLogger(__name__)


def create_error_response(message: str, status: int = 400) -> JsonResponse:
    """Helper to create consistent error responses"""
    return JsonResponse(
        {"error": message},
        status=status
    )


def create_telegram_response(channel_id: str, text: str) -> JsonResponse:
    """Helper to create Telegram bot responses"""
    reply = {
        "type": "message.create",
        "channelId": channel_id,
        "text": text
    }
    return JsonResponse(reply)


@csrf_exempt
@require_http_methods(["POST"])
def telex_expense_agent(request):
    """
    Telegram webhook endpoint for expense tracking.
    
    Expected payload:
    {
        "channelId": "...",
        "from": {"id": "..."},
        "text": "I spent ₦5000 on food"
    }
    """
    try:
        # Parse incoming request
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return create_error_response("Invalid JSON payload")
        
        # Extract required fields
        channel_id = payload.get("channelId")
        user_data = payload.get("from", {})
        user_id = user_data.get("id")
        text = payload.get("text", "").strip()
        
        # Validate required fields
        if not all([channel_id, user_id, text]):
            return create_error_response("Missing required fields: channelId, from.id, or text")
        
        # Log incoming request
        logger.info(f"Processing expense from user {user_id}: {text[:50]}...")
        
        # Parse the expense text
        parsed = parse_expense(text)
        
        if not parsed or "amount" not in parsed:
            return create_telegram_response(
                channel_id,
                "❌ Could not parse your expense. Please try:\n"
                "• 'I spent ₦5000 on food today'\n"
                "• 'Paid 2500 for transport yesterday'"
            )
        
        # Create expense record
        try:
            expense = Expense.objects.create(
                user_id=user_id,
                channel_id=channel_id,
                amount=parsed["amount"],
                category=parsed["category"],
                description=parsed.get("description", ""),
                date=parsed.get("date")
            )
            
            # Get weekly summary
            summary = get_weekly_summary(user_id)
            
            # Build success message
            reply_text = (
                f"✅ Logged ₦{parsed['amount']:,.2f} "
                f"for {parsed['category'].capitalize()} "
                f"on {parsed['date'].strftime('%b %d')}\n\n"
                f"{summary}"
            )
            
            logger.info(f"Successfully created expense {expense.id} for user {user_id}")
            return create_telegram_response(channel_id, reply_text)
            
        except ValidationError as ve:
            logger.warning(f"Validation error for user {user_id}: {ve}")
            return create_telegram_response(
                channel_id,
                f"❌ Invalid data: {str(ve)}"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in telex_expense_agent: {e}", exc_info=True)
        return create_error_response("Internal server error", status=500)


@require_http_methods(["GET"])
def telex_logs(request, channel_id):
    """
    Retrieve logs for debugging (should be protected in production).
    """
    # TODO: Add authentication
    log_file = "agent-logs.txt"
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = f.read()
        return HttpResponse(logs, content_type="text/plain")
    except FileNotFoundError:
        return HttpResponse("No logs available yet.", content_type="text/plain")


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        "status": "healthy",
        "service": "Finance IQ",
        "version": "1.0.0"
    })


@require_http_methods(["GET"])
def index(request):
    """Main page view - Dashboard or API documentation"""
    # Get some basic stats
    total_expenses = Expense.objects.count()
    total_users = Expense.objects.values('user_id').distinct().count()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Finance IQ - Expense Tracker</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 40px;
                padding: 40px 20px;
            }}
            .header h1 {{
                font-size: 3em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .header p {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            .stat-card {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
            }}
            .stat-card h3 {{
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .stat-card p {{
                color: #666;
                font-size: 1em;
            }}
            .endpoints {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .endpoints h2 {{
                color: #333;
                margin-bottom: 25px;
                font-size: 1.8em;
            }}
            .endpoint {{
                background: #f8f9fa;
                padding: 20px;
                margin: 15px 0;
                border-radius: 10px;
                border-left: 5px solid #667eea;
                transition: transform 0.2s;
            }}
            .endpoint:hover {{
                transform: translateX(5px);
            }}
            .endpoint h3 {{
                color: #667eea;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
            }}
            .endpoint p {{
                color: #666;
                margin: 5px 0;
            }}
            .method {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.85em;
                margin-right: 10px;
            }}
            .post {{ background: #28a745; color: white; }}
            .get {{ background: #007bff; color: white; }}
            code {{
                background: #2d3748;
                color: #68d391;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.9em;
                display: inline-block;
                margin-top: 10px;
            }}
            .example {{
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                overflow-x: auto;
            }}
            .status {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                background: #d4edda;
                border-radius: 10px;
                color: #155724;
                font-weight: bold;
                font-size: 1.2em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 Finance IQ</h1>
                <p>AI-Powered Expense Tracking via Telegram</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{total_expenses}</h3>
                    <p>Total Expenses</p>
                </div>
                <div class="stat-card">
                    <h3>{total_users}</h3>
                    <p>Active Users</p>
                </div>
            </div>
            
            <div class="endpoints">
                <h2>📡 API Endpoints</h2>
                
                <div class="endpoint">
                    <h3><span class="method post">POST</span> /a2a/financeiq/</h3>
                    <p>Telegram webhook for logging expenses</p>
                    <div class="example">
{{"channelId": "...", "from": {{"id": "..."}}, "text": "I spent ₦5000 on food today"}}
                    </div>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method get">GET</span> /api/health/</h3>
                    <p>Health check endpoint - verify service status</p>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method get">GET</span> /api/expenses/</h3>
                    <p>List all expenses (with optional filters)</p>
                    <code>?user_id=xxx&category=food&days=7</code>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method get">GET</span> /api/summary/&lt;user_id&gt;/</h3>
                    <p>Get expense summary for a specific user</p>
                    <code>Example: /api/summary/user_123456/</code>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method get">GET</span> /agent-logs/&lt;channel_id&gt;.txt</h3>
                    <p>View agent logs (admin only)</p>
                </div>
            </div>
            
            <div class="status">
                ✅ Service Running - All Systems Operational
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


@require_http_methods(["GET"])
def list_expenses(request):
    """
    List expenses with optional filters.
    Query params: user_id, category, days
    """
    user_id = request.GET.get('user_id')
    category = request.GET.get('category')
    days = request.GET.get('days', 30)
    
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    # Build query
    start_date = date.today() - timedelta(days=days)
    expenses = Expense.objects.filter(date__gte=start_date)
    
    if user_id:
        expenses = expenses.filter(user_id=user_id)
    if category:
        expenses = expenses.filter(category=category)
    
    # Serialize data
    data = []
    for exp in expenses.order_by('-date', '-created_at')[:100]:  # Limit to 100
        data.append({
            'id': exp.id,
            'user_id': exp.user_id,
            'amount': float(exp.amount),
            'category': exp.category,
            'description': exp.description,
            'date': exp.date.isoformat(),
            'created_at': exp.created_at.isoformat(),
        })
    
    return JsonResponse({
        'count': len(data),
        'expenses': data
    })


@require_http_methods(["GET"])
def get_summary(request, user_id):
    """Get expense summary for a specific user"""
    days = request.GET.get('days', 7)
    
    try:
        days = int(days)
    except ValueError:
        days = 7
    
    start_date = date.today() - timedelta(days=days)
    expenses = Expense.objects.filter(user_id=user_id, date__gte=start_date)
    
    if not expenses.exists():
        return JsonResponse({
            'user_id': user_id,
            'message': f'No expenses found in the last {days} days',
            'total': 0,
            'by_category': {}
        })
    
    # Calculate totals
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    by_category = (
        expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    category_data = {
        item['category']: float(item['total'])
        for item in by_category
    }
    
    return JsonResponse({
        'user_id': user_id,
        'period_days': days,
        'total': float(total),
        'by_category': category_data,
        'expense_count': expenses.count(),
        'summary_text': get_weekly_summary(user_id)
    })