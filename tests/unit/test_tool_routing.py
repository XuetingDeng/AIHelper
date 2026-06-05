from app.agents.planner_agent import PlannerAgent


def test_tool_routing_for_notion_prep():
    plan = PlannerAgent().plan("What should I prepare for my Notion recruiter call Friday?", "2026-06-05")
    assert "get_calendar_events" in plan.expected_tools
    assert "search_emails" in plan.expected_tools
    assert "read_notes" in plan.expected_tools
    assert plan.start_date == "2026-06-05"
