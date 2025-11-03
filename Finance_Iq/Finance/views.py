from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .parser import parse_expense
from .analytics import get_weekly_summary
from .models import Expense

import json, os

# Create your views here.


LOG_FILE = "agent-logs.txt"

def log_event(entry):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

@api_view
def telex_expense_agent(request):
    payload = request.data
    log_event({"incoming": payload})

    try:
        channel_id = payload.get("channelId")
        user_id = payload.get("from", {}).get("id")
        text = payload.get("text", "")

        if not (channel_id and text):
            return Response({"Error": "Invalid Payload"}, status=status.HTTP_400_BAD_REQUEST)
        
        parsed = parse_expense(text)
        if not parsed["amount"]:
            reply = {
                "type": "message.create",
                "channelId": channel_id,
                "text": "❌ Could not find an amount in your message. Try 'I spent ₦5000 on transport today'."
            }
            log_event({"outgoing": reply})
            return Response(reply)
        
        Expense = Expense.objects.create(
            user_id = user_id,
            channel_id = channel_id,
            amount = parsed["amount"],
            category = parsed["category"],
            description = parsed["description"],
            date = parsed["date"]
        )

        summary = get_weekly_summary(user_id)
        reply_text = (
            f"✅ Logged ₦{parsed['amount']:,.2f} for '{parsed['category'].capitalize()}' "
            f"on {parsed['date']}.\n\n{summary}"
        )

        reply = {
            "type": "message.create",
            "channelId": channel_id,
            "text": reply_text
        }
        log_event({"outgoing": reply})
        return Response(reply)
    
    except Exception as e:
        log_event({"Error": str(e)})
        return Response({"Error": "Server error", "message": str(e)}, status=500)
    

@api_view(["GET"])
def telex_logs(request, channel_id):
    if not os.path.exists(LOG_FILE):
        return Response("No logs yet.")
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return Response(f.read(), content_type="text/plain")
    
    
