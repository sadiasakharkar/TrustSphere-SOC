from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_event_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def reconstruct_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(events, key=lambda event: (_parse_event_time(event["event_time"]), event["event_id"]))
    timeline: list[dict[str, Any]] = []
    for index, event in enumerate(ordered, start=1):
        principal = event.get("principal", {})
        artifacts = event.get("artifacts", {})
        timeline.append(
            {
                "sequence": index,
                "event_id": event["event_id"],
                "event_time": event["event_time"],
                "event_kind": event.get("event_kind"),
                "severity": event.get("severity"),
                "src_ip": principal.get("src_ip"),
                "dest_ip": principal.get("dest_ip"),
                "user": principal.get("user_id") or principal.get("email"),
                "action": artifacts.get("action"),
                "protocol": artifacts.get("protocol"),
                "request_path": artifacts.get("request_path"),
                "duplicate_count": event.get("duplicate_count", 1),
            }
        )
    return timeline
