import pytest

from app.agents.planner_agent import PlannerAgent
from app.llm.client import MockLLMClient


def test_llm_planner_returns_expected_tools():
    llm = MockLLMClient(
        [
            {
                "intent": "meeting_or_deadline_prep",
                "start_date": "2026-06-05",
                "end_date": "2026-06-06",
                "keywords": ["notion"],
                "expected_tools": ["get_calendar_events", "search_emails"],
                "unsafe_actions": [],
                "draft_requested": False,
            }
        ]
    )
    plan = PlannerAgent(llm).plan("Prep for Notion call", "2026-06-05")
    assert plan.expected_tools == ["get_calendar_events", "search_emails"]
    assert plan.keywords == ["notion"]


def test_llm_planner_filters_invalid_tool_names():
    llm = MockLLMClient(
        [
            {
                "intent": "general_briefing",
                "start_date": "2026-06-05",
                "end_date": "2026-06-06",
                "keywords": [],
                "expected_tools": ["get_calendar_events", "send_email", "unknown_tool"],
                "unsafe_actions": [],
                "draft_requested": False,
            }
        ]
    )
    plan = PlannerAgent(llm).plan("What meetings do I have?", "2026-06-05")
    assert plan.expected_tools == ["get_calendar_events"]


def test_llm_planner_merges_deterministic_unsafe_detection():
    llm = MockLLMClient(
        [
            {
                "intent": "meeting_or_deadline_prep",
                "start_date": "2026-06-06",
                "end_date": "2026-06-06",
                "keywords": [],
                "expected_tools": ["get_calendar_events"],
                "unsafe_actions": [],
                "draft_requested": False,
            }
        ]
    )
    plan = PlannerAgent(llm).plan("Cancel my interview meeting tomorrow.", "2026-06-05")
    assert plan.intent == "unsafe_action"
    assert "cancel_calendar_event" in plan.unsafe_actions


def test_llm_planner_downgrades_unsupported_unsafe_intent():
    llm = MockLLMClient(
        [
            {
                "intent": "unsafe_action",
                "start_date": "2026-06-06",
                "end_date": "2026-06-06",
                "keywords": ["notion"],
                "expected_tools": ["get_calendar_events", "search_emails"],
                "unsafe_actions": ["send_email", "cancel_calendar_event"],
                "draft_requested": False,
            }
        ]
    )
    plan = PlannerAgent(llm).plan("Help me prepare for my Notion recruiter interview tomorrow.", "2026-06-05")
    assert plan.intent == "meeting_or_deadline_prep"
    assert plan.unsafe_actions == []


def test_llm_planner_raises_on_invalid_json():
    llm = MockLLMClient(["not json"])
    with pytest.raises(ValueError):
        PlannerAgent(llm).plan("What should I prepare for this week?", "2026-06-05")
