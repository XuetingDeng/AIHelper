from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def calendar_events() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "calendar_events.json")


def emails() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "emails.json")


def notes_text() -> str:
    return (DATA_DIR / "notes.md").read_text(encoding="utf-8")
