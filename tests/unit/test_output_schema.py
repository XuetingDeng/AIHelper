from app.orchestrator import Orchestrator
from app.llm.client import MockLLMClient
from app.schemas import AgentOutput


def test_output_schema_validity():
    llm = MockLLMClient(
        [
            {
                "intent": "general_briefing",
                "start_date": "2026-06-05",
                "end_date": "2026-06-06",
                "keywords": [],
                "expected_tools": [],
                "unsafe_actions": [],
                "draft_requested": False,
            },
            {
                "summary": "No tool-backed items requested.",
                "time_window": "2026-06-05 to 2026-06-06",
                "items": [],
                "blocked_actions": [],
            },
        ]
    )
    output = Orchestrator(llm_client=llm).run("What should I prepare for this week?", mode="optimized")
    parsed = AgentOutput.model_validate(output.model_dump())
    assert parsed.summary
    assert isinstance(parsed.items, list)
