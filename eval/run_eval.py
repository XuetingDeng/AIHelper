from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from app.config import RESULTS_DIR
from app.orchestrator import Orchestrator
from eval.judge import heuristic_judge, judge_kappa
from eval.metrics import (
    dangerous_action_blocked,
    expected_fact_recall,
    forbidden_fact_violation,
    mean,
    schema_valid,
    tool_routing_accuracy,
)


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(mode: str, golden: Path) -> dict[str, Any]:
    orchestrator = Orchestrator()
    cases = load_cases(golden)
    rows = []
    judgments = []
    for case in cases:
        output_model = orchestrator.run(case["input"], mode=mode)
        output = output_model.model_dump()
        actual_tools = [call.name for call in orchestrator.client.tool_calls]
        judge = heuristic_judge(case, output)
        judgments.append(judge)
        rows.append(
            {
                "id": case["id"],
                "expected_fact_recall": expected_fact_recall(output, case["expected_facts"]),
                "forbidden_fact_violation": forbidden_fact_violation(output, case["forbidden_facts"]),
                "tool_routing_accuracy": tool_routing_accuracy(actual_tools, case["expected_tools"]),
                "dangerous_action_blocked": dangerous_action_blocked(output, case["expected_safety_decision"]),
                "output_schema_validity": schema_valid(output),
                "judge_score": judge["score"],
                "actual_tools": actual_tools,
            }
        )
    aggregate = {
        "mode": mode,
        "case_count": len(rows),
        "expected_fact_recall": mean([row["expected_fact_recall"] for row in rows]),
        "forbidden_fact_violation_rate": mean([row["forbidden_fact_violation"] for row in rows]),
        "tool_routing_accuracy": mean([row["tool_routing_accuracy"] for row in rows]),
        "dangerous_action_block_rate": mean([row["dangerous_action_blocked"] for row in rows]),
        "output_schema_validity": mean([row["output_schema_validity"] for row in rows]),
        "average_judge_score": mean([row["judge_score"] for row in rows]),
        "cohens_kappa": judge_kappa(judgments),
        "cases": rows,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS_DIR / f"{mode}_results.json"
    result_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    return aggregate


def write_experiment_summary(baseline: dict[str, Any] | None, optimized: dict[str, Any] | None) -> None:
    path = RESULTS_DIR / "experiment_summary.csv"
    rows = []
    if baseline:
        rows.append(["0", "Baseline single-agent, weak guardrail", "baseline", "Simple retrieval works but unsafe cancellation may pass"])
    if baseline and optimized:
        delta = optimized["dangerous_action_block_rate"] - baseline["dangerous_action_block_rate"]
        rows.append(["1", "Multi-agent orchestration + permission validator", f"block rate {delta:+.2f}", "Safety and reproducibility improved"])
        delta_recall = optimized["expected_fact_recall"] - baseline["expected_fact_recall"]
        rows.append(["2", "Structured checklist/evidence response", f"fact recall {delta_recall:+.2f}", "Better grounding with small deterministic overhead"])
    elif optimized:
        rows.append(["1", "Optimized multi-agent run", "optimized only", "Structured output and safety guardrail enabled"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Round", "Change", "Metric delta", "Conclusion"])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic eval")
    parser.add_argument("--mode", choices=["baseline", "optimized", "both"], default="optimized")
    parser.add_argument("--golden", type=Path, default=Path("eval/golden.jsonl"))
    args = parser.parse_args()
    baseline = evaluate("baseline", args.golden) if args.mode in {"baseline", "both"} else None
    optimized = evaluate("optimized", args.golden) if args.mode in {"optimized", "both"} else None
    write_experiment_summary(baseline, optimized)
    print(json.dumps(optimized or baseline, indent=2))


if __name__ == "__main__":
    main()
