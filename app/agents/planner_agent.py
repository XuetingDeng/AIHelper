from __future__ import annotations

from datetime import date, timedelta

from app.schemas import Plan
from app.tools.permission_tools import detect_requested_actions


TOOL_KEYWORDS = {
    "get_calendar_events": ["meeting", "calendar", "call", "deadline", "tomorrow", "week", "friday", "saturday", "interview"],
    "search_emails": ["email", "recruiter", "notion", "project", "deadline", "follow-up", "follow up", "important", "study"],
    "read_notes": ["notes", "prepare", "prep", "project", "capstone", "checklist", "rubric", "presentation"],
}


def _window(query: str, today: str) -> tuple[str, str]:
    current = date.fromisoformat(today)
    q = query.lower()
    if "tomorrow" in q:
        target = current + timedelta(days=1)
        return target.isoformat(), target.isoformat()
    if "friday" in q:
        return "2026-06-05", "2026-06-05"
    if "saturday" in q:
        return "2026-06-06", "2026-06-06"
    if "week" in q:
        return current.isoformat(), (current + timedelta(days=7)).isoformat()
    return current.isoformat(), (current + timedelta(days=3)).isoformat()


def _keywords(query: str) -> list[str]:
    known = ["notion", "recruiter", "capstone", "ai", "resume", "study", "professor", "deadline", "interview"]
    found = [word for word in known if word in query.lower()]
    return found


class PlannerAgent:
    def plan(self, query: str, today: str) -> Plan:
        q = query.lower()
        start_date, end_date = _window(q, today)
        expected_tools = [
            tool for tool, terms in TOOL_KEYWORDS.items() if any(term in q for term in terms)
        ]
        if not expected_tools:
            expected_tools = ["get_calendar_events", "search_emails", "read_notes"]
        if "draft" in q or "follow-up" in q or "follow up" in q:
            expected_tools = sorted(set(expected_tools + ["search_emails", "read_notes"]))
        unsafe_actions = detect_requested_actions(query)
        intent = "unsafe_action" if unsafe_actions else "meeting_or_deadline_prep"
        return Plan(
            intent=intent,
            start_date=start_date,
            end_date=end_date,
            keywords=_keywords(query),
            expected_tools=expected_tools,
            unsafe_actions=unsafe_actions,
            draft_requested="draft" in q or "follow-up" in q or "follow up" in q,
        )
