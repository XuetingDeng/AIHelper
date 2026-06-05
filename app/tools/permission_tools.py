from __future__ import annotations

from app.schemas import BlockedAction


DANGEROUS_ACTIONS = {
    "send_email": ["send", "email sent", "send the email"],
    "cancel_calendar_event": ["cancel", "delete meeting", "remove meeting"],
    "reschedule_calendar_event": ["reschedule", "move my meeting", "change the time"],
    "delete_note": ["delete note", "delete notes", "remove note", "remove notes"],
}


def detect_requested_actions(user_query: str) -> list[str]:
    query = user_query.lower()
    actions: list[str] = []
    for action, phrases in DANGEROUS_ACTIONS.items():
        if any(phrase in query for phrase in phrases):
            actions.append(action)
    if ("delete" in query or "remove" in query) and ("note" in query or "notes" in query):
        actions.append("delete_note")
    actions = list(dict.fromkeys(actions))
    return actions


def validate_permission(action_type: str, user_query: str) -> tuple[bool, BlockedAction | None]:
    if action_type in DANGEROUS_ACTIONS:
        return False, BlockedAction(
            action=action_type,
            reason="requires explicit user confirmation and is blocked in this mock agent",
        )
    if action_type == "draft_email":
        return True, None
    return True, None
