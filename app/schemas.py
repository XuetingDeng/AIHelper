from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Mode = Literal["baseline", "optimized"]
Priority = Literal["low", "medium", "high"]
Source = Literal["calendar", "email", "notes"]


class AgentInput(BaseModel):
    query: str
    mode: Mode = "optimized"
    today: str = "2026-06-05"


class BriefingItem(BaseModel):
    title: str
    date: str
    source: Source
    priority: Priority
    evidence: list[str] = Field(default_factory=list)
    prep_checklist: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    safe_next_actions: list[str] = Field(default_factory=list)


class BlockedAction(BaseModel):
    action: str
    reason: str


class AgentOutput(BaseModel):
    summary: str
    time_window: str
    items: list[BriefingItem] = Field(default_factory=list)
    blocked_actions: list[BlockedAction] = Field(default_factory=list)


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "error"] = "ok"
    result_count: int = 0
    error: str | None = None


class Plan(BaseModel):
    intent: str
    start_date: str
    end_date: str
    keywords: list[str] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)
    unsafe_actions: list[str] = Field(default_factory=list)
    draft_requested: bool = False


class EvidenceRecord(BaseModel):
    title: str
    date: str
    source: Source
    facts: list[str]
    raw: dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    query: str
    mode: Mode
    tools_called: list[ToolCall]
    blocked_actions: list[BlockedAction]
    latency_ms: int
    output_schema_valid: bool
