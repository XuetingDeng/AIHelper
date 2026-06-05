from __future__ import annotations

from app.mcp_server.client import MCPClient


def get_calendar_events(client: MCPClient, start_date: str, end_date: str, keywords: list[str] | None = None) -> list[dict]:
    return client.get_calendar_events(start_date, end_date, keywords)
