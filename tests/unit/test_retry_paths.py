from app.mcp_server.client import MCPClient


class BrokenServer:
    def get_calendar_events(self, **kwargs):
        raise RuntimeError("temporary failure")


def test_client_records_tool_error_and_returns_empty_list():
    client = MCPClient(server=BrokenServer())
    assert client.get_calendar_events("2026-06-05", "2026-06-06") == []
    assert client.tool_calls[-1].status == "error"
