from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from correlation.attack_graph.evidence_bundle import build_evidence_bundle, summarize_incident
from correlation.entity_resolution.deduplicator import merge_duplicate_alerts
from correlation.entity_resolution.event_signature import build_incident_key
from correlation.models.incident import IncidentRecord
from correlation.timeline_reconstruction.timeline_builder import reconstruct_timeline


SEVERITY_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _severity_max(events: list[dict[str, Any]]) -> str:
    severities = [str(event.get("severity", "unknown")) for event in events]
    return max(severities, key=lambda item: SEVERITY_ORDER.get(item, 0)) if severities else "unknown"


def _incident_entities(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for event in events:
        principal = event.get("principal", {})
        artifacts = event.get("artifacts", {})
        for name, value in (
            ("users", principal.get("user_id") or principal.get("email")),
            ("src_ips", principal.get("src_ip")),
            ("dest_ips", principal.get("dest_ip")),
            ("hosts", principal.get("hostname")),
            ("protocols", artifacts.get("protocol")),
            ("actions", artifacts.get("action")),
        ):
            if value:
                buckets[name].add(str(value))
    return {name: sorted(values) for name, values in buckets.items()}


def _incident_type(events: list[dict[str, Any]]) -> str:
    kinds = {str(event.get("event_kind", "unknown")) for event in events}
    if "alert" in kinds:
        return "alert_cluster"
    if "network" in kinds and "application" in kinds:
        return "multi_stage_network_application"
    if "network" in kinds:
        return "network_incident"
    if "email" in kinds:
        return "email_incident"
    return "generic_incident"


def _parse_event_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _cluster_by_time(events: list[dict[str, Any]], window_minutes: int = 20) -> list[list[dict[str, Any]]]:
    if not events:
        return []
    ordered = sorted(events, key=lambda item: _parse_event_time(item["event_time"]))
    clusters: list[list[dict[str, Any]]] = [[ordered[0]]]
    window = timedelta(minutes=window_minutes)
    for event in ordered[1:]:
        previous = clusters[-1][-1]
        if _parse_event_time(event["event_time"]) - _parse_event_time(previous["event_time"]) <= window:
            clusters[-1].append(event)
        else:
            clusters.append([event])
    return clusters


def build_incidents(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped_events, duplicate_map = merge_duplicate_alerts(events)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in deduped_events:
        grouped[build_incident_key(event)].append(event)

    incidents: list[dict[str, Any]] = []
    incident_index = 1
    for grouped_events in grouped.values():
        for incident_events in _cluster_by_time(grouped_events):
            timeline = reconstruct_timeline(incident_events)
            evidence = build_evidence_bundle(incident_events)
            severity = _severity_max(incident_events)
            event_confidences = [float(event.get("confidence", 0.0)) for event in incident_events]
            max_confidence = max(event_confidences)
            mean_confidence = sum(event_confidences) / len(event_confidences)
            severity_boost = 0.1 if severity == "critical" else 0.05 if severity == "high" else 0.0
            chain_boost = 0.05 if len(incident_events) >= 3 else 0.02 if len(incident_events) == 2 else 0.0
            confidence = min(1.0, round((max_confidence * 0.6) + (mean_confidence * 0.25) + severity_boost + chain_boost, 4))
            related_ids = [event["event_id"] for event in incident_events]
            merged_ids = []
            for event_id in related_ids:
                merged_ids.extend(duplicate_map.get(event_id, []))

            incident = IncidentRecord(
                incident_id=f"INC-{incident_index:05d}",
                incident_type=_incident_type(incident_events),
                status="open",
                severity=severity,
                confidence=round(confidence, 4),
                start_time=timeline[0]["event_time"],
                end_time=timeline[-1]["event_time"],
                entities=_incident_entities(incident_events),
                timeline=timeline,
                evidence_bundle=evidence,
                related_event_ids=related_ids,
                merged_duplicates=sorted(set(merged_ids)),
                summary=summarize_incident(incident_events),
            )
            incidents.append(incident.to_dict())
            incident_index += 1

    incidents.sort(key=lambda item: (SEVERITY_ORDER.get(item["severity"], 0), item["start_time"]), reverse=True)
    return incidents
