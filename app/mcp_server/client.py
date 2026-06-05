from __future__ import annotations

from typing import Any

from app.mcp_server.server import MockMCPServer
from app.schemas import ToolCall


class MCPClient:
    def __init__(self, server: MockMCPServer | None = None) -> None:
        self.server = server or MockMCPServer()
        self.tool_calls: list[ToolCall] = []

    def reset(self) -> None:
        self.tool_calls.clear()

    def _record(self, name: str, args: dict[str, Any], status: str, result_count: int, error: str | None = None) -> None:
        self.tool_calls.append(
            ToolCall(name=name, args=args, status=status, result_count=result_count, error=error)
        )

    def get_calendar_events(self, start_date: str, end_date: str, keywords: list[str] | None = None) -> list[dict[str, Any]]:
        args = {"start_date": start_date, "end_date": end_date, "keywords": keywords}
        try:
            result = self.server.get_calendar_events(**args)
            self._record("get_calendar_events", args, "ok", len(result))
            return result
        except Exception as exc:
            self._record("get_calendar_events", args, "error", 0, str(exc))
            return []

    def search_emails(self, query: str, tags: list[str] | None = None, start_date: str | None = None, end_date: str | None = None) -> list[dict[str, Any]]:
        args = {"query": query, "tags": tags, "start_date": start_date, "end_date": end_date}
        try:
            result = self.server.search_emails(**args)
            self._record("search_emails", args, "ok", len(result))
            return result
        except Exception as exc:
            self._record("search_emails", args, "error", 0, str(exc))
            return []

    def read_notes(self, query: str | None = None) -> list[dict[str, str]]:
        args = {"query": query}
        try:
            result = self.server.read_notes(**args)
            self._record("read_notes", args, "ok", len(result))
            return result
        except Exception as exc:
            self._record("read_notes", args, "error", 0, str(exc))
            return []
