from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from feedback_loop.analyst_feedback.feedback_models import AnalystFeedbackRecord


def append_feedback(record: AnalystFeedbackRecord, path: str | Path = Path("feedback_loop/analyst_feedback/feedback_log.jsonl")) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def load_feedback(path: str | Path = Path("feedback_loop/analyst_feedback/feedback_log.jsonl")) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    records: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records
