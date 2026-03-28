from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from feedback_loop.retraining_signals.signal_builder import build_feedback_signal_map


def export_retraining_examples(
    priority_records: list[dict[str, Any]],
    feedback_records: list[dict[str, Any]],
    path: str | Path = Path("feedback_loop/retraining_signals/retraining_examples.jsonl"),
) -> int:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    signal_map = build_feedback_signal_map(priority_records, feedback_records)
    count = 0
    with destination.open("w", encoding="utf-8") as handle:
        for record in priority_records:
            signal = signal_map.get(record["incident_id"])
            if not signal:
                continue
            payload = {
                "incident_id": record["incident_id"],
                "priority_score": record["priority_score"],
                "priority_label": record["priority_label"],
                "incident": record["incident"],
                "feedback_signal": signal,
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            count += 1
    return count
