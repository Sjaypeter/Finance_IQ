import re
from datetime import datetime, timedelta


def parse_expense(text: str):
    # Parses text like:
    """I spent ₦5000 on food yesterday" → amount, category, date"""

    #Extra amount
    amount_match = re.search(r"[₦$]?\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)", text)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else None

    #Extract category
    categories = ["food", "transport", "entertainment", "shopping", "bills"]
    category = next((c for c in categories if c in text.lower()), "other")

    # detect date keywords
    today = datetime.today().date()
    if "yesterday" in text.lower():
        date = today - timedelta(days=1)
    elif "today" in text.lower():
        date = today
    else:
        date = today

    # extract description
    description = re.sub(r"[₦$]?\s?\d+(?:,\d{3})*(?:\.\d{1,2})?", "", text)
    description = description.replace("spent", "").strip()

    return {"amount": amount, "category": category, "date": date, "description": description}