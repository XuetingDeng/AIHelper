from app.orchestrator import Orchestrator
from app.schemas import AgentOutput


def test_output_schema_validity():
    output = Orchestrator().run("What should I prepare for this week?", mode="optimized")
    parsed = AgentOutput.model_validate(output.model_dump())
    assert parsed.summary
    assert isinstance(parsed.items, list)
