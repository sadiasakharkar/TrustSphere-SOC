from __future__ import annotations

from typing import Any


def serialize_incident_for_llm(priority_record: dict[str, Any]) -> dict[str, Any]:
    incident = priority_record["incident"]
    structured_evidence = []
    for evidence in incident.get("evidence_bundle", []):
        structured_evidence.append(
            {
                "event_id": evidence.get("event_id"),
                "event_time": evidence.get("event_time"),
                "event_kind": evidence.get("event_kind"),
                "severity": evidence.get("severity"),
                "confidence": evidence.get("confidence"),
                "principal": evidence.get("principal"),
                "artifacts": {
                    "protocol": evidence.get("artifacts", {}).get("protocol"),
                    "action": evidence.get("artifacts", {}).get("action"),
                    "request_path": evidence.get("artifacts", {}).get("request_path"),
                    "bytes_transferred": evidence.get("artifacts", {}).get("bytes_transferred"),
                },
                "labels": evidence.get("labels"),
                "anomaly": evidence.get("anomaly"),
            }
        )

    return {
        "incident_id": incident["incident_id"],
        "priority": {
            "score": priority_record["priority_score"],
            "label": priority_record["priority_label"],
            "confidence": incident["confidence"],
            "reasons": priority_record["reasons"],
        },
        "incident_window": {
            "start_time": incident["start_time"],
            "end_time": incident["end_time"],
        },
        "entities": incident.get("entities", {}),
        "timeline": incident.get("timeline", []),
        "summary": incident.get("summary", {}),
        "structured_evidence": structured_evidence,
    }
