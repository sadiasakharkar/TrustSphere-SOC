from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from correlation.incident_builder import build_incidents
from ingestion.adapters.normalize_records import ingest_and_normalize
from playbook_generation.recommendations.playbook_generator import generate_playbook_for_incident
from prefiltering.rules.risk_rules import evaluate_risk_rules
from prioritization.ranking.prioritize_incidents import prioritize_incidents

from backend.config import settings
from backend.state import UploadRecord, utc_now


def infer_dataset_id(filename: str, override: str | None = None) -> str:
    if override:
        return override
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return settings.default_csv_dataset_id
    return settings.default_json_dataset_id


def persist_upload(
    *,
    filename: str,
    content: bytes,
    content_type: str | None,
    uploaded_by: str,
    dataset_id: str,
    domain: str,
) -> UploadRecord:
    upload_id = f"UPL-{uuid4().hex[:12]}"
    suffix = Path(filename).suffix.lower()
    destination = settings.uploads_dir / f"{upload_id}{suffix}"
    destination.write_bytes(content)
    return UploadRecord(
        upload_id=upload_id,
        filename=filename,
        stored_path=str(destination),
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
        content_type=content_type,
        dataset_id=dataset_id,
        domain=domain,
        uploaded_by=uploaded_by,
        uploaded_at=utc_now(),
        processing_notes=["File accepted and staged for normalization."],
    )


def normalize_upload(record: UploadRecord) -> dict[str, Any]:
    events = list(
        ingest_and_normalize(
            record.stored_path,
            dataset_id=record.dataset_id,
            domain=record.domain,
        )
    )
    label_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    suspicious_events: list[dict[str, Any]] = []

    for event in events:
        rule_eval = evaluate_risk_rules(event)
        labels = dict(event.get("labels", {}))
        labels["prefilter_label"] = rule_eval.label
        labels["rule_score"] = rule_eval.score
        labels["rule_reasons"] = rule_eval.reasons
        event["labels"] = labels
        if not event.get("confidence"):
            event["confidence"] = round(rule_eval.score / 100.0, 4)
        severity_counts[str(event.get("severity", "unknown"))] += 1
        label_counts[rule_eval.label] += 1
        if rule_eval.label != "false_positive" or str(event.get("severity", "unknown")) in {"high", "critical"}:
            suspicious_events.append(event)

    record.normalized_events = events
    record.suspicious_events = suspicious_events
    record.status = "normalized"
    record.processing_notes.append("Canonical normalization completed with rule-based explainability labels.")
    if not suspicious_events:
        record.processing_notes.append("No suspicious events crossed the incident generation threshold.")

    return {
        "upload_id": record.upload_id,
        "status": record.status,
        "normalized_event_count": len(events),
        "suspicious_event_count": len(suspicious_events),
        "label_counts": dict(label_counts),
        "severity_counts": dict(severity_counts),
    }


def generate_incident_records(record: UploadRecord) -> dict[str, Any]:
    if not record.normalized_events:
        normalize_upload(record)

    incidents = build_incidents(record.suspicious_events)
    priority_records = prioritize_incidents(incidents, feedback_path=None)
    record.incidents = incidents
    record.priority_records = priority_records
    record.status = "incidents_generated"
    record.processing_notes.append("Incident clustering and prioritization completed.")

    return {
        "upload_id": record.upload_id,
        "status": record.status,
        "incident_count": len(priority_records),
        "top_incident_id": priority_records[0]["incident_id"] if priority_records else None,
    }


def indicator_summary(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {
        "source_ips": set(),
        "destination_ips": set(),
        "users": set(),
        "protocols": set(),
        "request_paths": set(),
    }
    for event in events:
        principal = event.get("principal", {})
        artifacts = event.get("artifacts", {})
        for key, value in (
            ("source_ips", principal.get("src_ip")),
            ("destination_ips", principal.get("dest_ip")),
            ("users", principal.get("user_id") or principal.get("email")),
            ("protocols", artifacts.get("protocol")),
            ("request_paths", artifacts.get("request_path")),
        ):
            if value:
                buckets[key].add(str(value))
    return {key: sorted(values)[:10] for key, values in buckets.items()}


def _flatten_rule_reasons(priority_record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    seen: set[str] = set()
    for evidence in priority_record["incident"].get("evidence_bundle", []):
        for reason in evidence.get("labels", {}).get("rule_reasons", []):
            if reason not in seen:
                seen.add(reason)
                reasons.append(reason)
    return reasons


def recommend_actions(priority_record: dict[str, Any]) -> list[dict[str, Any]]:
    incident = priority_record["incident"]
    entities = incident.get("entities", {})
    severity = str(incident.get("severity", "unknown"))
    actions: list[dict[str, Any]] = [
        {
            "title": "Validate scope against affected assets and users",
            "why": "Confirm whether the same principals and hosts appear across the full incident timeline.",
            "approval_required": False,
        }
    ]
    if entities.get("src_ips") or entities.get("dest_ips"):
        actions.append(
            {
                "title": "Review east-west and ingress/egress traffic around flagged IPs",
                "why": "Cross-boundary communication is a strong triage signal for suspicious network activity.",
                "approval_required": False,
            }
        )
    if severity in {"high", "critical"}:
        actions.append(
            {
                "title": "Prepare containment recommendation for analyst approval",
                "why": "High-severity incidents should be ready for isolation, blocking, or credential control actions.",
                "approval_required": True,
            }
        )
    return actions


def build_explanation(priority_record: dict[str, Any]) -> dict[str, Any]:
    incident = priority_record["incident"]
    evidence_bundle = incident.get("evidence_bundle", [])
    return {
        "incident_id": priority_record["incident_id"],
        "what": {
            "incident_type": incident.get("incident_type"),
            "severity": incident.get("severity"),
            "confidence": incident.get("confidence"),
            "summary": incident.get("summary"),
            "entities": incident.get("entities"),
        },
        "how": {
            "timeline": incident.get("timeline", []),
            "triggered_rules": _flatten_rule_reasons(priority_record),
            "priority_breakdown": priority_record.get("score_breakdown", {}),
            "priority_reasons": priority_record.get("reasons", []),
        },
        "why": {
            "decision": (
                f"Incident {priority_record['incident_id']} was ranked {priority_record['priority_label']} "
                f"because of severity, asset context, recurrence, and rule-based signal evidence."
            ),
            "indicator_summary": indicator_summary(evidence_bundle),
            "evidence_count": len(evidence_bundle),
            "supporting_event_ids": incident.get("related_event_ids", []),
        },
        "recommended_next_steps": recommend_actions(priority_record),
    }


def build_monitoring_summary(record: UploadRecord | None) -> dict[str, Any]:
    if record is None:
        return {
            "upload_id": None,
            "status": "idle",
            "message": "No uploads have been processed yet.",
            "security_notes": [
                "Authentication uses server-side session invalidation.",
                "Enable HTTPS/TLS in production and mark cookies as Secure.",
            ],
        }

    severity_counts = Counter(str(event.get("severity", "unknown")) for event in record.normalized_events)
    label_counts = Counter(str(event.get("labels", {}).get("prefilter_label", "unknown")) for event in record.normalized_events)
    top_alerts = []
    for priority_record in record.priority_records[:5]:
        incident = priority_record["incident"]
        top_alerts.append(
            {
                "incident_id": priority_record["incident_id"],
                "title": incident.get("incident_type"),
                "priority_label": priority_record.get("priority_label"),
                "priority_score": priority_record.get("priority_score"),
                "severity": incident.get("severity"),
                "confidence": incident.get("confidence"),
                "entities": incident.get("entities"),
                "why": priority_record.get("reasons", []),
            }
        )

    return {
        "upload_id": record.upload_id,
        "status": record.status,
        "filename": record.filename,
        "dataset_id": record.dataset_id,
        "uploaded_at": record.uploaded_at.isoformat(),
        "normalized_event_count": len(record.normalized_events),
        "suspicious_event_count": len(record.suspicious_events),
        "incident_count": len(record.priority_records),
        "severity_counts": dict(severity_counts),
        "label_counts": dict(label_counts),
        "top_alerts": top_alerts,
        "indicators": indicator_summary(record.suspicious_events),
        "security_notes": [
            "Server-side session invalidation is enforced on logout.",
            "Authentication cookies are HttpOnly and should be Secure under HTTPS/TLS in production.",
            "Each incident includes explainable rule reasons, score breakdowns, and source evidence references.",
        ],
    }


def playbook_for_record(record: UploadRecord, incident_id: str) -> dict[str, Any]:
    if incident_id in record.playbooks:
        return record.playbooks[incident_id]
    priority_record = next((item for item in record.priority_records if item["incident_id"] == incident_id), None)
    if priority_record is None:
        raise KeyError(incident_id)
    playbook = generate_playbook_for_incident(priority_record, provider=settings.llm_provider or "ollama")
    record.playbooks[incident_id] = playbook
    return playbook


def save_analyst_feedback(priority_record: dict[str, Any], verdict: str, notes: str | None) -> dict[str, Any]:
    incident = priority_record["incident"]
    return {
        "incident_id": priority_record["incident_id"],
        "verdict": verdict,
        "notes": notes or "",
        "timestamp": utc_now().isoformat(),
        "entities": incident.get("entities", {}),
        "summary": incident.get("summary", {}),
    }
