from __future__ import annotations

from app.mcp_server.client import MCPClient


def search_emails(client: MCPClient, query: str, tags: list[str] | None = None, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    return client.search_emails(query=query, tags=tags, start_date=start_date, end_date=end_date)
