from app.mcp_server.client import MCPClient


def test_notes_retrieval_by_keyword():
    notes = MCPClient().read_notes("capstone")
    assert notes
    assert any("Capstone" in note["title"] for note in notes)
