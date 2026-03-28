from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from correlation.entity_resolution.event_signature import build_dedup_signature


def _parse_event_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def merge_duplicate_alerts(events: list[dict[str, Any]], window_minutes: int = 10) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    deduped: list[dict[str, Any]] = []
    duplicate_map: dict[str, list[str]] = {}
    latest_by_signature: dict[str, dict[str, Any]] = {}
    window = timedelta(minutes=window_minutes)

    for event in sorted(events, key=lambda item: item.get("event_time", "")):
        signature = build_dedup_signature(event)
        current_time = _parse_event_time(event["event_time"])
        previous = latest_by_signature.get(signature)
        if previous is None:
            copied = dict(event)
            copied["duplicate_count"] = 1
            copied["merged_duplicate_ids"] = []
            deduped.append(copied)
            latest_by_signature[signature] = copied
            duplicate_map[copied["event_id"]] = []
            continue

        previous_time = _parse_event_time(previous["event_time"])
        if abs(current_time - previous_time) <= window:
            previous["duplicate_count"] = int(previous.get("duplicate_count", 1)) + 1
            previous.setdefault("merged_duplicate_ids", []).append(event["event_id"])
            duplicate_map.setdefault(previous["event_id"], []).append(event["event_id"])
            previous["confidence"] = max(float(previous.get("confidence", 0.0)), float(event.get("confidence", 0.0)))
            continue

        copied = dict(event)
        copied["duplicate_count"] = 1
        copied["merged_duplicate_ids"] = []
        deduped.append(copied)
        latest_by_signature[signature] = copied
        duplicate_map[copied["event_id"]] = []

    return deduped, duplicate_map
