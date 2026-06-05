from __future__ import annotations

from datetime import date
from typing import Any

from app.mcp_server import mock_data


def _as_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _contains_keywords(text: str, keywords: list[str] | None) -> bool:
    if not keywords:
        return True
    text_l = text.lower()
    return any(keyword.lower() in text_l for keyword in keywords if keyword)


class MockMCPServer:
    def get_calendar_events(
        self,
        start_date: str,
        end_date: str,
        keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        start = _as_date(start_date)
        end = _as_date(end_date)
        results = []
        for event in mock_data.calendar_events():
            event_date = _as_date(event["start"])
            haystack = " ".join(
                [event["title"], event["description"], " ".join(event.get("tags", []))]
            )
            if start <= event_date <= end and _contains_keywords(haystack, keywords):
                results.append(event)
        return results

    def search_emails(
        self,
        query: str,
        tags: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        query_terms = [term for term in query.lower().split() if len(term) > 2]
        results = []
        for email in mock_data.emails():
            if start_date and _as_date(email["date"]) < _as_date(start_date):
                continue
            if end_date and _as_date(email["date"]) > _as_date(end_date):
                continue
            if tags and not set(tags).intersection(email.get("tags", [])):
                continue
            haystack = f"{email['from']} {email['subject']} {email['body']} {' '.join(email.get('tags', []))}".lower()
            if not query_terms or any(term in haystack for term in query_terms):
                results.append(email)
        return results

    def read_notes(self, query: str | None = None) -> list[dict[str, str]]:
        text = mock_data.notes_text()
        sections = []
        for block in text.split("\n# "):
            clean = block.strip()
            if not clean:
                continue
            if not clean.startswith("#"):
                clean = "# " + clean
            title = clean.splitlines()[0].replace("#", "").strip()
            body = "\n".join(clean.splitlines()[1:]).strip()
            if query and query.lower() not in f"{title} {body}".lower():
                continue
            sections.append({"title": title, "body": body})
        return sections
