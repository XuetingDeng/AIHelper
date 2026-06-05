from __future__ import annotations

import json
from datetime import date
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

class PlannerAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def plan(self, query: str, today: str) -> Plan:
        return self._llm_plan(query, today)

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
        expected_tools = [
            tool for tool in raw.get("expected_tools", []) if tool in ALLOWED_TOOLS
        ]
        unsafe_actions = [
            action
            for action in detect_requested_actions(query)
            if action in ALLOWED_UNSAFE_ACTIONS
        ]
        start_date = str(raw["start_date"])
        end_date = str(raw["end_date"])
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
        intent = str(raw["intent"])
        if unsafe_actions:
            intent = "unsafe_action"
        elif intent == "unsafe_action":
            intent = "meeting_or_deadline_prep"
        elif intent not in {"meeting_or_deadline_prep", "general_briefing"}:
            raise ValueError(f"Invalid planner intent: {intent}")
        keywords = [str(keyword) for keyword in raw.get("keywords", [])]
        return Plan(
            intent=intent,
            start_date=start_date,
            end_date=end_date,
            keywords=keywords,
            expected_tools=expected_tools,
            unsafe_actions=unsafe_actions,
            draft_requested=bool(raw.get("draft_requested", False)),
        )
