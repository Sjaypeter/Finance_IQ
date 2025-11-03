import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
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
    return JsonResponse({"status": "healthy"})