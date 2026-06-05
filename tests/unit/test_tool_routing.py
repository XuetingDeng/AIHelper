from app.agents.planner_agent import PlannerAgent
from app.llm.client import MockLLMClient


def test_tool_routing_for_notion_prep():
    llm = MockLLMClient(
        [
            {
                "intent": "meeting_or_deadline_prep",
                "start_date": "2026-06-05",
                "end_date": "2026-06-05",
                "keywords": ["notion", "recruiter"],
                "expected_tools": ["get_calendar_events", "search_emails", "read_notes"],
                "unsafe_actions": [],
                "draft_requested": False,
            }
        ]
    )
    plan = PlannerAgent(llm).plan("What should I prepare for my Notion recruiter call Friday?", "2026-06-05")
    assert "get_calendar_events" in plan.expected_tools
    assert "search_emails" in plan.expected_tools
    assert "read_notes" in plan.expected_tools
    assert plan.start_date == "2026-06-05"
