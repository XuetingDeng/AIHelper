# Architecture

```mermaid
flowchart TD
  U[User Query] --> O[Orchestrator]
  O --> P[LLM PlannerAgent]
  O --> R[RetrieverAgent]
  O --> S[Deterministic RiskSafetyAgent]
  O --> A[LLM ResponseAgent]
  R --> M[MCP-like Client]
  M --> C[get_calendar_events]
  M --> E[search_emails]
  M --> N[read_notes]
  S --> G[Permission Guard]
  A --> J[Structured JSON]
  O --> L[Audit Log]
  J --> V[Eval Harness]
```

By default the implementation can run deterministically with mock local data. When `--llm` is enabled, PlannerAgent and ResponseAgent use the OpenAI API for structured JSON generation, while RetrieverAgent still performs MCP/tool calls and RiskSafetyAgent remains deterministic for safety.
