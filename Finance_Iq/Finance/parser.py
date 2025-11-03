import re
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any


def parse_expense(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse natural language expense text.
    
    Example inputs:
        "I spent ₦5000 on food yesterday"
        "₦2500 for transport today"
        "spent 10000 on entertainment"
    
    Returns:
        Dict with keys: amount, category, date, description
        None if parsing fails
    """
    if not text or not isinstance(text, str):
        return None
    
    text_lower = text.lower().strip()
    
    # Extract amount - handles ₦, N prefix or just numbers
    amount_patterns = [
        r'[₦N]\s*(\d+(?:[,]\d{3})*(?:\.\d{2})?)',  # ₦5,000 or N5000
        r'(\d+(?:[,]\d{3})*(?:\.\d{2})?)\s*naira',  # 5000 naira
        r'(?:spent|paid|cost)\s+(\d+(?:[,]\d{3})*(?:\.\d{2})?)',  # spent 5000
    ]
    
    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                break
            except ValueError:
                continue
    
    if amount is None:
        return None
    
    # Extract category - check for keywords
    category_keywords = {
        "food": ["food", "breakfast", "lunch", "dinner", "meal", "restaurant", "grocery"],
        "transport": ["transport", "uber", "taxi", "fuel", "gas", "bus", "train"],
        "entertainment": ["entertainment", "movie", "cinema", "game", "concert", "party"],
        "shopping": ["shopping", "clothes", "shoes", "shop", "store", "mall"],
        "bills": ["bills", "electricity", "water", "rent", "internet", "phone", "subscription"],
    }
    
    category = "other"
    for cat, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            category = cat
            break
    
    # Extract date - handle relative dates
    today = date.today()
    expense_date = today
    
    if "yesterday" in text_lower:
        expense_date = today - timedelta(days=1)
    elif "today" in text_lower or "just now" in text_lower:
        expense_date = today
    # Add more date parsing as needed (e.g., "last week", specific dates)
    
    # Extract description - remove amount and common phrases
    description = text
    # Remove amount mentions
    description = re.sub(r'[₦N]\s*\d+(?:[,]\d{3})*(?:\.\d{2})?', '', description)
    description = re.sub(r'\d+(?:[,]\d{3})*(?:\.\d{2})?\s*naira', '', description)
    # Remove common phrases
    for phrase in ["i spent", "spent", "paid", "on", "for", "yesterday", "today"]:
        description = description.replace(phrase, "")
    description = description.strip()
    
    return {
        "amount": amount,
        "category": category,
        "date": expense_date,
        "description": description if description else f"{category.capitalize()} expense"
    }