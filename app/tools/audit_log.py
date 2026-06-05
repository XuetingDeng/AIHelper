from __future__ import annotations

import json

from app.config import AUDIT_LOG_PATH
from app.schemas import RunRecord


def write_audit_log(run_record: RunRecord) -> None:
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run_record.model_dump(), ensure_ascii=False) + "\n")
