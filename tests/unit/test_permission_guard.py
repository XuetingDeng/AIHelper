from app.orchestrator import Orchestrator
from app.llm.client import MockLLMClient
from app.tools.permission_tools import validate_permission


def test_permission_guard_blocks_cancel():
    allowed, blocked = validate_permission("cancel_calendar_event", "Cancel my meeting tomorrow")
    assert not allowed
    assert blocked is not None


def test_permission_detection_blocks_delete_notes():
    from app.tools.permission_tools import detect_requested_actions

    assert "delete_note" in detect_requested_actions("Delete the capstone notes.")


def test_optimized_never_claims_cancel_success():
    llm = MockLLMClient(
        [
            {
                "intent": "meeting_or_deadline_prep",
                "start_date": "2026-06-06",
                "end_date": "2026-06-06",
                "keywords": ["interview"],
                "expected_tools": ["get_calendar_events"],
                "unsafe_actions": [],
                "draft_requested": False,
            },
            {
                "summary": "The unsafe calendar write was blocked.",
                "time_window": "2026-06-06 to 2026-06-06",
                "items": [],
                "blocked_actions": [],
            },
        ]
    )
    output = Orchestrator(llm_client=llm).run("Cancel my interview meeting tomorrow.", mode="optimized")
    text = str(output.model_dump()).lower()
    assert output.blocked_actions
    assert "cancelled successfully" not in text
