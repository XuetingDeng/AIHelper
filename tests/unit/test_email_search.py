from app.mcp_server.client import MCPClient


def test_email_search_finds_recruiter_email():
    emails = MCPClient().search_emails("Notion recruiter")
    assert any(email["from"] == "caris@notion.so" for email in emails)
