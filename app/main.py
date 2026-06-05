from __future__ import annotations

import argparse
import json

from app.config import DEFAULT_TODAY
from app.orchestrator import Orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Deadline & Meeting Prep Agent")
    parser.add_argument("--mode", choices=["baseline", "optimized"], default="optimized")
    parser.add_argument("--query", required=True)
    parser.add_argument("--today", default=DEFAULT_TODAY)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = Orchestrator().run(args.query, mode=args.mode, today=args.today)
    print(json.dumps(output.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
