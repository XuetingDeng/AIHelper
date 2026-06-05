from __future__ import annotations

from app.mcp_server.client import MCPClient
from app.schemas import EvidenceRecord, Plan
from app.tools.calendar_tools import get_calendar_events
from app.tools.email_tools import search_emails
from app.tools.notes_tools import read_notes


class RetrieverAgent:
    def __init__(self, client: MCPClient) -> None:
        self.client = client

    def retrieve(self, plan: Plan, query: str) -> list[EvidenceRecord]:
        records: list[EvidenceRecord] = []
        if "get_calendar_events" in plan.expected_tools:
            for event in get_calendar_events(self.client, plan.start_date, plan.end_date, plan.keywords or None):
                records.append(
                    EvidenceRecord(
                        title=event["title"],
                        date=event["start"][:10],
                        source="calendar",
                        facts=[event["description"], f"Location: {event['location']}", f"Tags: {', '.join(event.get('tags', []))}"],
                        raw=event,
                    )
                )
        if "search_emails" in plan.expected_tools:
            for email in search_emails(self.client, " ".join(plan.keywords) or query, start_date=None, end_date=plan.end_date):
                records.append(
                    EvidenceRecord(
                        title=email["subject"],
                        date=email["date"],
                        source="email",
                        facts=[f"From: {email['from']}", email["body"]],
                        raw=email,
                    )
                )
        if "read_notes" in plan.expected_tools:
            note_query = plan.keywords[0] if plan.keywords else None
            notes = read_notes(self.client, note_query)
            if not notes and note_query:
                notes = read_notes(self.client, None)
            for note in notes:
                records.append(
                    EvidenceRecord(
                        title=note["title"],
                        date=plan.start_date,
                        source="notes",
                        facts=[note["body"]],
                        raw=note,
                    )
                )
        return records
