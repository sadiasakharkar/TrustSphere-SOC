from __future__ import annotations

from typing import Any

from correlation.models.incident import EvidenceItem

SEVERITY_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def build_evidence_bundle(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for event in events:
        evidence.append(
            EvidenceItem(
                event_id=event["event_id"],
                event_time=event["event_time"],
                event_kind=event.get("event_kind", "unknown"),
                severity=event.get("severity", "unknown"),
                confidence=float(event.get("confidence", 0.0)),
                principal=event.get("principal", {}),
                artifacts=event.get("artifacts", {}),
                labels=event.get("labels", {}),
                anomaly=event.get("anomaly"),
                raw_ref=event.get("raw_ref"),
            ).to_dict()
        )
    return evidence


def summarize_incident(events: list[dict[str, Any]]) -> dict[str, Any]:
    severities = [str(event.get("severity", "unknown")) for event in events]
    event_kinds = [str(event.get("event_kind", "unknown")) for event in events]
    duplicate_total = sum(int(event.get("duplicate_count", 1)) for event in events)
    anomaly_scores = [
        float(event.get("anomaly", {}).get("final_score", event.get("anomaly", {}).get("normalized_score", 0.0)))
        for event in events
        if event.get("anomaly")
    ]
    return {
        "event_count": len(events),
        "duplicate_total": duplicate_total,
        "max_severity": max(severities, key=lambda item: SEVERITY_ORDER.get(item, 0)) if severities else "unknown",
        "event_kinds": sorted(set(event_kinds)),
        "average_anomaly_score": round(sum(anomaly_scores) / len(anomaly_scores), 4) if anomaly_scores else 0.0,
    }
