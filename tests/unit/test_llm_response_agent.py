from app.agents.response_agent import ResponseAgent
from app.llm.client import MockLLMClient
from app.schemas import BlockedAction, EvidenceRecord, Plan


def _plan() -> Plan:
    return Plan(
        intent="meeting_or_deadline_prep",
        start_date="2026-06-05",
        end_date="2026-06-06",
        keywords=["notion"],
        expected_tools=["get_calendar_events"],
        unsafe_actions=[],
        draft_requested=False,
    )


def _records() -> list[EvidenceRecord]:
    return [
        EvidenceRecord(
            title="Notion Recruiter Intro Call",
            date="2026-06-05",
            source="calendar",
            facts=["Intro call for Software Engineer, New Grad role"],
        )
    ]


def test_llm_response_returns_agent_output():
    llm = MockLLMClient(
        [
            {
                "summary": "Prepare for the Notion recruiter call.",
                "time_window": "2026-06-05 to 2026-06-06",
                "items": [
                    {
                        "title": "Notion Recruiter Intro Call",
                        "date": "2026-06-05",
                        "source": "calendar",
                        "priority": "high",
                        "evidence": ["Intro call for Software Engineer, New Grad role"],
                        "prep_checklist": ["Prepare questions"],
                        "risks": ["Weak preparation may reduce interview signal"],
                        "safe_next_actions": ["Draft notes only"],
                    }
                ],
                "blocked_actions": [],
            }
        ]
    )
    output = ResponseAgent(llm).build(_plan(), _records(), [], {"Notion Recruiter Intro Call": "high"})
    assert output.items[0].title == "Notion Recruiter Intro Call"
    assert output.items[0].prep_checklist == ["Prepare questions"]


def test_llm_response_preserves_blocked_actions():
    blocked = [
        BlockedAction(
            action="cancel_calendar_event",
            reason="requires explicit user confirmation and is blocked in this mock agent",
        )
    ]
    llm = MockLLMClient(
        [
            {
                "summary": "The unsafe request was blocked.",
                "time_window": "2026-06-05 to 2026-06-06",
                "items": [],
                "blocked_actions": [],
            }
        ]
    )
    output = ResponseAgent(llm).build(_plan(), _records(), blocked, {})
    assert output.blocked_actions == blocked


def test_llm_response_drops_ungrounded_items():
    llm = MockLLMClient(
        [
            {
                "summary": "Briefing",
                "time_window": "2026-06-05 to 2026-06-06",
                "items": [
                    {
                        "title": "Invented Meeting",
                        "date": "2026-06-05",
                        "source": "calendar",
                        "priority": "high",
                        "evidence": ["made up"],
                        "prep_checklist": ["do something"],
                        "risks": ["risk"],
                        "safe_next_actions": ["suggestion"],
                    }
                ],
                "blocked_actions": [],
            }
        ]
    )
    output = ResponseAgent(llm).build(_plan(), _records(), [], {})
    assert output.items == []


def test_llm_response_falls_back_on_unsafe_success_claim():
    llm = MockLLMClient(
        [
            {
                "summary": "Meeting cancelled successfully.",
                "time_window": "2026-06-05 to 2026-06-06",
                "items": [],
                "blocked_actions": [],
            }
        ]
    )
    output = ResponseAgent(llm).build(_plan(), _records(), [], {"Notion Recruiter Intro Call": "high"})
    assert "cancelled successfully" not in str(output.model_dump()).lower()
    assert output.items
