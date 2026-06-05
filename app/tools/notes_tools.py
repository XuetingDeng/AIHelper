from __future__ import annotations

from app.mcp_server.client import MCPClient


def read_notes(client: MCPClient, query: str | None = None) -> list[dict[str, str]]:
    return client.read_notes(query)
