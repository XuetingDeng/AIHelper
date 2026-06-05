from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "app" / "data"
EVAL_DIR = ROOT_DIR / "eval"
RESULTS_DIR = EVAL_DIR / "results"
AUDIT_LOG_PATH = ROOT_DIR / "audit_log.jsonl"
DEFAULT_TODAY = "2026-06-05"
