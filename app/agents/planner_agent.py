from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from app.llm.client import LLMClient
from app.schemas import Plan
from app.tools.permission_tools import detect_requested_actions


ALLOWED_TOOLS = {"get_calendar_events", "search_emails", "read_notes"}
ALLOWED_UNSAFE_ACTIONS = {
    "send_email",
    "cancel_calendar_event",
    "reschedule_calendar_event",
    "delete_note",
}

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
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def plan(self, query: str, today: str) -> Plan:
        if self.llm_client:
            try:
                return self._llm_plan(query, today)
            except Exception:
                return self._deterministic_plan(query, today)
        return self._deterministic_plan(query, today)

    def _deterministic_plan(self, query: str, today: str) -> Plan:
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

    def _llm_plan(self, query: str, today: str) -> Plan:
        system_prompt = (
            "You are the planner agent for an AI Deadline & Meeting Prep Agent. "
            "Convert the user request into a structured execution plan. You do not answer the user. "
            "You only decide intent, time window, keywords, expected read-only tools, unsafe requested actions, "
            "and whether a draft was requested. Allowed read-only tools: get_calendar_events, search_emails, read_notes. "
            "Dangerous/write actions include send_email, cancel_calendar_event, reschedule_calendar_event, delete_note. "
            "Never include write actions in expected_tools."
        )
        schema = {
            "intent": "meeting_or_deadline_prep | unsafe_action | general_briefing",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "keywords": ["string"],
            "expected_tools": ["get_calendar_events", "search_emails", "read_notes"],
            "unsafe_actions": [
                "send_email",
                "cancel_calendar_event",
                "reschedule_calendar_event",
                "delete_note",
            ],
            "draft_requested": False,
        }
        user_prompt = (
            f"today: {today}\n"
            f"user query: {query}\n"
            f"allowed tools: {sorted(ALLOWED_TOOLS)}\n"
            f"required JSON schema: {json.dumps(schema)}"
        )
        raw = self.llm_client.complete_json(system_prompt, user_prompt)
        return self._sanitize_llm_plan(raw, query, today)

    def _sanitize_llm_plan(self, raw: dict[str, Any], query: str, today: str) -> Plan:
        fallback = self._deterministic_plan(query, today)
        expected_tools = [
            tool for tool in raw.get("expected_tools", []) if tool in ALLOWED_TOOLS
        ]
        if not expected_tools:
            expected_tools = fallback.expected_tools
        unsafe_actions = [
            action
            for action in raw.get("unsafe_actions", [])
            if action in ALLOWED_UNSAFE_ACTIONS
        ]
        for action in detect_requested_actions(query):
            if action not in unsafe_actions:
                unsafe_actions.append(action)
        start_date = str(raw.get("start_date", fallback.start_date))
        end_date = str(raw.get("end_date", fallback.end_date))
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
        intent = str(raw.get("intent", fallback.intent))
        if unsafe_actions:
            intent = "unsafe_action"
        elif intent not in {"meeting_or_deadline_prep", "general_briefing"}:
            intent = fallback.intent
        keywords = [str(keyword) for keyword in raw.get("keywords", fallback.keywords)]
        return Plan(
            intent=intent,
            start_date=start_date,
            end_date=end_date,
            keywords=keywords,
            expected_tools=expected_tools,
            unsafe_actions=unsafe_actions,
            draft_requested=bool(raw.get("draft_requested", fallback.draft_requested)),
        )
