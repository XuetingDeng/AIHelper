from app.mcp_server.client import MCPClient


def test_calendar_filtering_by_date_and_keyword():
    client = MCPClient()
    events = client.get_calendar_events("2026-06-06", "2026-06-06", ["capstone"])
    assert len(events) == 1
    assert events[0]["title"] == "AI Capstone Project Review"
