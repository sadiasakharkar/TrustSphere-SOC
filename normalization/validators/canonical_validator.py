from __future__ import annotations

from typing import Any


REQUIRED_TOP_LEVEL_FIELDS = (
    "event_id",
    "event_time",
    "ingest_time",
    "source",
    "raw_format",
    "event_kind",
    "severity",
    "confidence",
    "artifacts",
    "labels",
    "raw_ref",
)


def validate_canonical_event(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
    confidence = payload.get("confidence")
    if confidence is not None and not (0.0 <= confidence <= 1.0):
        errors.append("confidence must be between 0.0 and 1.0")
    return errors
