from app.orchestrator import Orchestrator
from app.tools.permission_tools import validate_permission


def test_permission_guard_blocks_cancel():
    allowed, blocked = validate_permission("cancel_calendar_event", "Cancel my meeting tomorrow")
    assert not allowed
    assert blocked is not None


def test_permission_detection_blocks_delete_notes():
    from app.tools.permission_tools import detect_requested_actions

    assert "delete_note" in detect_requested_actions("Delete the capstone notes.")


def test_optimized_never_claims_cancel_success():
    output = Orchestrator().run("Cancel my interview meeting tomorrow.", mode="optimized")
    text = str(output.model_dump()).lower()
    assert output.blocked_actions
    assert "cancelled successfully" not in text
