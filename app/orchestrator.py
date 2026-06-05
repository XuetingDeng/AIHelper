from __future__ import annotations

import time

from app.agents.planner_agent import PlannerAgent
from app.agents.response_agent import ResponseAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.risk_agent import RiskSafetyAgent
from app.config import DEFAULT_TODAY
from app.llm.client import LLMClient, OpenAILLMClient
from app.mcp_server.client import MCPClient
from app.schemas import AgentOutput, BlockedAction, BriefingItem, Plan, RunRecord
from app.tools.audit_log import write_audit_log
from app.tools.permission_tools import detect_requested_actions


class Orchestrator:
    def __init__(
        self,
        client: MCPClient | None = None,
        llm_client: LLMClient | None = None,
        use_llm: bool = False,
    ) -> None:
        self.client = client or MCPClient()
        active_llm_client = llm_client or (OpenAILLMClient() if use_llm else None)
        self.planner = PlannerAgent(active_llm_client)
        self.risk = RiskSafetyAgent()
        self.response = ResponseAgent(active_llm_client)

    def run(self, query: str, mode: str = "optimized", today: str = DEFAULT_TODAY) -> AgentOutput:
        started = time.perf_counter()
        self.client.reset()
        if mode == "baseline":
            output = self._run_baseline(query, today)
        else:
            output = self._run_optimized(query, today)
        latency_ms = int((time.perf_counter() - started) * 1000)
        record = RunRecord(
            query=query,
            mode=mode,  # type: ignore[arg-type]
            tools_called=self.client.tool_calls,
            blocked_actions=output.blocked_actions,
            latency_ms=latency_ms,
            output_schema_valid=True,
        )
        write_audit_log(record)
        return output

    def _run_optimized(self, query: str, today: str) -> AgentOutput:
        plan = self.planner.plan(query, today)
        records = RetrieverAgent(self.client).retrieve(plan, query)
        blocked = self.risk.blocked_actions(plan.unsafe_actions, query)
        priorities = {record.title: self.risk.priority(record, today) for record in records}
        return self.response.build(plan, records, blocked, priorities)

    def _run_baseline(self, query: str, today: str) -> AgentOutput:
        plan = Plan(
            intent="baseline",
            start_date=today,
            end_date="2026-06-12",
            keywords=[],
            expected_tools=["get_calendar_events", "search_emails", "read_notes"],
            unsafe_actions=detect_requested_actions(query),
            draft_requested="draft" in query.lower(),
        )
        records = RetrieverAgent(self.client).retrieve(plan, query)
        items = [
            BriefingItem(
                title=record.title,
                date=record.date,
                source=record.source,
                priority="medium",
                evidence=record.facts[:1],
                prep_checklist=["Review this item"],
                risks=["Baseline mode does not deeply analyze risk"],
                safe_next_actions=["Suggestion only"],
            )
            for record in records[:8]
        ]
        blocked: list[BlockedAction] = []
        if plan.unsafe_actions and "cancel" not in query.lower():
            blocked = [
                BlockedAction(action=action, reason="baseline noticed a risky action")
                for action in plan.unsafe_actions
            ]
        return AgentOutput(
            summary=f"Baseline found {len(items)} item(s).",
            time_window=f"{plan.start_date} to {plan.end_date}",
            items=items,
            blocked_actions=blocked,
        )
