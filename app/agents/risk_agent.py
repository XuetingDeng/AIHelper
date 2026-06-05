from __future__ import annotations

from app.config import DEFAULT_TODAY
from app.schemas import BlockedAction, EvidenceRecord
from app.tools.permission_tools import validate_permission
from app.tools.priority_tools import classify_priority


class RiskSafetyAgent:
    def blocked_actions(self, unsafe_actions: list[str], query: str) -> list[BlockedAction]:
        blocked: list[BlockedAction] = []
        for action in unsafe_actions:
            allowed, block = validate_permission(action, query)
            if not allowed and block:
                blocked.append(block)
        return blocked

    def priority(self, record: EvidenceRecord, today: str = DEFAULT_TODAY) -> str:
        payload = record.raw.copy()
        payload["date"] = record.date
        payload["facts"] = " ".join(record.facts)
        return classify_priority(payload, today)
