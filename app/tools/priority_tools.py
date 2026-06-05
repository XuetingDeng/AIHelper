from __future__ import annotations

from datetime import date
from typing import Any

from app.config import DEFAULT_TODAY
from app.schemas import Priority


HIGH_TERMS = {"deadline", "interview", "recruiter", "important", "due", "capstone"}


def classify_priority(item: dict[str, Any], today: str = DEFAULT_TODAY) -> Priority:
    text = " ".join(str(value) for value in item.values()).lower()
    item_date = str(item.get("date") or item.get("start") or today)[:10]
    days_until = (date.fromisoformat(item_date) - date.fromisoformat(today)).days
    if days_until <= 1 and any(term in text for term in HIGH_TERMS):
        return "high"
    if days_until <= 3 or any(term in text for term in HIGH_TERMS):
        return "medium"
    return "low"
