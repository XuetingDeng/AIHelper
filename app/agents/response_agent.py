from __future__ import annotations

import json
from typing import Any

from app.llm.client import LLMClient
from app.schemas import AgentOutput, BlockedAction, BriefingItem, EvidenceRecord, Plan


FORBIDDEN_CLAIMS = [
    "cancelled successfully",
    "email sent",
    "meeting deleted",
    "calendar updated",
]


class ResponseAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def build(self, plan: Plan, records: list[EvidenceRecord], blocked: list[BlockedAction], priorities: dict[str, str]) -> AgentOutput:
        return self._llm_build(plan, records, blocked, priorities)

    def _llm_build(self, plan: Plan, records: list[EvidenceRecord], blocked: list[BlockedAction], priorities: dict[str, str]) -> AgentOutput:
        system_prompt = (
            "You are the response agent for an AI Deadline & Meeting Prep Agent. "
            "Generate a concise, safe, evidence-grounded meeting/deadline briefing. "
            "You must only use the provided evidence records. Do not invent meetings, deadlines, emails, or notes. "
            "If blocked_actions is non-empty, clearly state that the unsafe write action was blocked and suggest safe next steps. "
            "You cannot claim that an email was sent, a meeting was cancelled, or a calendar was modified."
        )
        schema = {
            "summary": "string",
            "time_window": "YYYY-MM-DD to YYYY-MM-DD",
            "items": [
                {
                    "title": "string",
                    "date": "YYYY-MM-DD",
                    "source": "calendar | email | notes",
                    "priority": "high | medium | low",
                    "evidence": ["string"],
                    "prep_checklist": ["string"],
                    "risks": ["string"],
                    "safe_next_actions": ["string"],
                }
            ],
            "blocked_actions": [blocked_action.model_dump() for blocked_action in blocked],
        }
        evidence = [
            {
                "title": record.title,
                "date": record.date,
                "source": record.source,
                "facts": record.facts,
                "priority": priorities.get(record.title, "medium"),
            }
            for record in records
        ]
        user_prompt = (
            f"plan: {plan.model_dump_json()}\n"
            f"evidence records: {json.dumps(evidence, ensure_ascii=False)}\n"
            f"blocked actions: {json.dumps([item.model_dump() for item in blocked], ensure_ascii=False)}\n"
            f"priorities: {json.dumps(priorities, ensure_ascii=False)}\n"
            f"required JSON schema: {json.dumps(schema, ensure_ascii=False)}"
        )
        raw = self.llm_client.complete_json(system_prompt, user_prompt)
        return self._sanitize_llm_output(raw, plan, records, blocked, priorities)

    def _sanitize_llm_output(
        self,
        raw: dict[str, Any],
        plan: Plan,
        records: list[EvidenceRecord],
        blocked: list[BlockedAction],
        priorities: dict[str, str],
    ) -> AgentOutput:
        if _contains_forbidden_claim(raw):
            raise ValueError("LLM output contained a forbidden success claim")
        grounded = {(record.title, record.source): record for record in records}
        items: list[BriefingItem] = []
        for item in raw.get("items", []):
            if not isinstance(item, dict):
                continue
            key = (str(item.get("title", "")), str(item.get("source", "")))
            record = grounded.get(key)
            if not record:
                continue
            payload = {
                "title": record.title,
                "date": str(item.get("date") or record.date),
                "source": record.source,
                "priority": priorities.get(record.title, item.get("priority", "medium")),
                "evidence": _string_list(item.get("evidence")),
                "prep_checklist": _string_list(item.get("prep_checklist")),
                "risks": _string_list(item.get("risks")),
                "safe_next_actions": _string_list(item.get("safe_next_actions")),
            }
            items.append(BriefingItem.model_validate(payload))
        summary = str(raw.get("summary") or f"Found {len(items)} relevant item(s).")
        if blocked and "blocked" not in summary.lower():
            summary += " Unsafe write action was blocked."
        return AgentOutput(
            summary=summary,
            time_window=f"{plan.start_date} to {plan.end_date}",
            items=items,
            blocked_actions=blocked,
        )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _contains_forbidden_claim(value: Any) -> bool:
    text = str(value).lower()
    return any(claim in text for claim in FORBIDDEN_CLAIMS)
