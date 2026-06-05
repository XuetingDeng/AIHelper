from __future__ import annotations

from app.schemas import AgentOutput, BlockedAction, BriefingItem, EvidenceRecord, Plan


def _checklist(record: EvidenceRecord, draft_requested: bool = False) -> list[str]:
    text = f"{record.title} {' '.join(record.facts)}".lower()
    if draft_requested:
        return ["Draft a concise follow-up email", "Confirm next steps before sending"]
    if "recruiter" in text or "notion" in text:
        return ["Prepare a 60-second introduction", "Review the Software Engineer New Grad role", "Write 3 questions for the recruiter"]
    if "capstone" in text or "project" in text:
        return ["Run baseline and optimized eval", "Prepare architecture and metric table", "Practice the demo script"]
    if "resume" in text:
        return ["Update project links", "Tighten new-grad summary", "Submit before 5 PM"]
    return ["Review source details", "Write open questions", "Confirm any needed materials"]


def _risks(record: EvidenceRecord) -> list[str]:
    text = f"{record.title} {' '.join(record.facts)}".lower()
    risks = []
    if "deadline" in text or "due" in text:
        risks.append("Deadline could be missed without same-day action")
    if "interview" in text or "recruiter" in text:
        risks.append("Weak preparation may reduce interview signal")
    if not risks:
        risks.append("Context may be incomplete because only mock local data is used")
    return risks


class ResponseAgent:
    def build(self, plan: Plan, records: list[EvidenceRecord], blocked: list[BlockedAction], priorities: dict[str, str]) -> AgentOutput:
        items: list[BriefingItem] = []
        seen: set[tuple[str, str]] = set()
        for record in records:
            key = (record.title, record.source)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                BriefingItem(
                    title=record.title,
                    date=record.date,
                    source=record.source,
                    priority=priorities.get(record.title, "medium"),
                    evidence=record.facts[:2],
                    prep_checklist=_checklist(record, plan.draft_requested),
                    risks=_risks(record),
                    safe_next_actions=["Suggest only; ask for confirmation before any write action"],
                )
            )
        high_count = sum(1 for item in items if item.priority == "high")
        summary = f"Found {len(items)} relevant item(s) from {plan.start_date} to {plan.end_date}; {high_count} high priority."
        if blocked:
            summary += " Unsafe write action was blocked."
        return AgentOutput(
            summary=summary,
            time_window=f"{plan.start_date} to {plan.end_date}",
            items=items,
            blocked_actions=blocked,
        )
