from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anomaly_detection.models.entity_anomaly_ensemble import EntityAnomalyEnsemble
from anomaly_detection.scoring.entity_behavior_scorer import score_entity_behavior
from correlation.incident_builder import build_incidents
from ingestion.loaders.file_loader import load_records
from normalization.mappers.canonical_mapper import canonicalize_record
from normalization.validators.canonical_validator import validate_canonical_event
from prefiltering.pipeline import PrefilteringPipeline
from prioritization.ranking.prioritize_incidents import prioritize_incidents


MODEL_SEARCH_ROOTS = (
    ROOT / "seed_models",
    ROOT / "artifacts",
)
ASSET_CONTEXT_PATH = ROOT / "configs" / "asset_context.json"


def _resolve_prefilter_dir() -> Path:
    for root in MODEL_SEARCH_ROOTS:
        candidate = root / "prefiltering"
        if (candidate / "prefilter_primary.joblib").exists() and (candidate / "prefilter_anomaly.joblib").exists():
            return candidate
    raise FileNotFoundError("No prefiltering model directory found in artifacts/ or seed_models/")


def _resolve_entity_model() -> Path:
    for root in MODEL_SEARCH_ROOTS:
        candidate = root / "anomaly_detection" / "entity_anomaly_ensemble.joblib"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No entity anomaly model found in artifacts/ or seed_models/")


def _classification_label(label: str) -> str:
    mapping = {
        "true_positive": "True Positive",
        "false_positive": "False Positive",
        "uncertain": "Uncertain",
    }
    return mapping.get(label, "Uncertain")


def _severity_tone(value: str) -> str:
    normalized = str(value or "unknown").lower()
    if normalized == "critical":
        return "critical"
    if normalized == "high":
        return "high"
    return "uncertain"


def _canonical_row(record: dict[str, Any], path: Path, dataset_id: str, domain: str, row_number: int) -> dict[str, Any]:
    event = canonicalize_record(
        record,
        dataset_id=dataset_id,
        dataset_path=str(path),
        source_type="file",
        domain=domain,
        raw_format=path.suffix.lower().lstrip(".") or "unknown",
        archive_member=None,
        row_number=row_number,
    ).to_dict()
    errors = validate_canonical_event(event)
    if errors:
        event["normalization_errors"] = errors
    return event


def _model_row(event: dict[str, Any]) -> dict[str, Any]:
    principal = event.get("principal", {})
    artifacts = event.get("artifacts", {})
    feature_map = artifacts.get("feature_map", {})
    return {
        "source_ip": principal.get("src_ip"),
        "src_ip": principal.get("src_ip"),
        "dest_ip": principal.get("dest_ip"),
        "destination_ip": principal.get("dest_ip"),
        "protocol": artifacts.get("protocol"),
        "proto": artifacts.get("protocol"),
        "action": artifacts.get("action"),
        "decision": artifacts.get("action"),
        "log_type": event.get("source", {}).get("source_type") or feature_map.get("log_type") or event.get("event_kind"),
        "event_category": event.get("event_kind"),
        "user_agent": artifacts.get("user_agent"),
        "ua": artifacts.get("user_agent"),
        "request_path": artifacts.get("request_path"),
        "uri": artifacts.get("request_path"),
        "bytes_transferred": artifacts.get("bytes_transferred"),
        "bytes_out": artifacts.get("bytes_transferred"),
        "subject": artifacts.get("subject"),
        "body": artifacts.get("body"),
        "urls": artifacts.get("urls"),
        **feature_map,
    }


def _event_log_line(evidence: dict[str, Any]) -> str:
    principal = evidence.get("principal", {})
    artifacts = evidence.get("artifacts", {})
    labels = evidence.get("labels", {})
    anomaly = evidence.get("anomaly") or {}
    return (
        f"{evidence.get('event_time')} "
        f"{evidence.get('event_kind')} "
        f"src={principal.get('src_ip') or '-'} "
        f"dest={principal.get('dest_ip') or '-'} "
        f"action={artifacts.get('action') or '-'} "
        f"severity={evidence.get('severity') or 'unknown'} "
        f"prefilter={labels.get('prefilter_label') or 'unknown'} "
        f"anomaly={int(round(float(anomaly.get('final_score', 0.0)) * 100))}%"
    )


def _incident_title(priority_record: dict[str, Any], file_name: str) -> str:
    incident = priority_record["incident"]
    entities = incident.get("entities", {})
    actions = entities.get("actions", [])
    hosts = entities.get("hosts", [])
    users = entities.get("users", [])
    anchor = actions[0] if actions else incident.get("incident_type", "incident")
    subject = users[0] if users else hosts[0] if hosts else file_name
    return f"{anchor} activity detected for {subject}"


def _incident_summary(priority_record: dict[str, Any], file_name: str) -> str:
    incident = priority_record["incident"]
    summary = incident.get("summary", {})
    return (
        f"{summary.get('event_count', 0)} correlated events from {file_name} were grouped into one "
        f"{incident.get('incident_type', 'incident')} with {incident.get('severity', 'unknown')} severity. "
        f"TrustSphere prioritized it using live prefilter, anomaly, and asset-context scoring."
    )


def _incident_evidence(priority_record: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_bundle = priority_record["incident"].get("evidence_bundle", [])
    result: list[dict[str, Any]] = []
    for evidence in evidence_bundle[:5]:
        labels = evidence.get("labels", {})
        anomaly = evidence.get("anomaly") or {}
        result.append(
            {
                "signal": evidence.get("event_kind", "unknown"),
                "observation": (
                    f"{evidence.get('artifacts', {}).get('action') or 'observed'} · "
                    f"prefilter={labels.get('prefilter_label') or 'unknown'} · "
                    f"anomaly={int(round(float(anomaly.get('final_score', 0.0)) * 100))}%"
                ),
                "contribution": min(100, max(10, int(round(float(evidence.get('confidence', 0.0)) * 100)))),
            }
        )
    return result


def _risk_breakdown(priority_record: dict[str, Any]) -> list[dict[str, Any]]:
    breakdown = priority_record.get("score_breakdown", {})
    return [
        {"label": "Prefilter", "value": int(round(float(breakdown.get("prefilter", 0.0)) * 100)), "color": "var(--primary)"},
        {"label": "Anomaly", "value": int(round(float(breakdown.get("anomaly", 0.0)) * 100)), "color": "var(--error)"},
        {"label": "Severity", "value": int(round(float(breakdown.get("severity", 0.0)) * 100)), "color": "var(--tertiary-container)"},
        {"label": "Asset Context", "value": int(round(float(breakdown.get("asset_context", 0.0)) * 100)), "color": "var(--secondary)"},
    ]


def _incident_stages(priority_record: dict[str, Any]) -> list[dict[str, Any]]:
    event_kinds = priority_record["incident"].get("summary", {}).get("event_kinds", [])
    stage_map = {
        "identity": ("Initial Access", "Identity activity"),
        "endpoint": ("Execution", "Host execution"),
        "application": ("Application Abuse", "App-layer event"),
        "network": ("Network Access", "Traffic inspection"),
        "alert": ("Detection", "Security alert"),
        "email": ("Mailbox Activity", "Email event"),
    }
    stages = []
    for index, event_kind in enumerate(event_kinds[:4]):
        name, sub = stage_map.get(event_kind, ("Analysis", event_kind))
        stages.append({"name": name, "sub": sub, "color": "var(--primary)" if index == 0 else "var(--tertiary-container)"})
    return stages or [{"name": "Analysis", "sub": "Correlated incident", "color": "var(--primary)"}]


def _incident_actions(priority_record: dict[str, Any], file_name: str) -> list[dict[str, str]]:
    reasons = priority_record.get("reasons", [])
    return [
        {"name": "Review correlated raw events", "why": f"Confirms how {file_name} produced this incident chain.", "urgency": "High"},
        {"name": "Validate top scoring signals", "why": ", ".join(reasons[:2]) if reasons else "Checks why the incident ranked highly.", "urgency": "Medium"},
        {"name": "Escalate if corroborated", "why": "Preserves analyst control while acting on real scored evidence.", "urgency": "Low"},
    ]


def _serialize_priority_record(priority_record: dict[str, Any], file_name: str, total_rows: int) -> dict[str, Any]:
    incident = priority_record["incident"]
    entities = incident.get("entities", {})
    evidence_bundle = incident.get("evidence_bundle", [])
    severity = _severity_tone(incident.get("severity"))
    priority_score = int(round(float(priority_record.get("priority_score", 0.0)) * 100))
    confidence = int(round(float(incident.get("confidence", 0.0)) * 100))
    who = (
        (entities.get("users") or [None])[0]
        or (entities.get("hosts") or [None])[0]
        or (entities.get("src_ips") or [None])[0]
        or file_name
    )

    return {
        "id": priority_record["incident_id"],
        "title": _incident_title(priority_record, file_name),
        "severity": severity,
        "risk": priority_score,
        "confidence": confidence,
        "who": who,
        "environment": f"{incident.get('incident_type', 'incident')} · {file_name}",
        "time": incident.get("start_time", "Current batch"),
        "summary": _incident_summary(priority_record, file_name),
        "tags": [incident.get("severity", "unknown"), priority_record.get("priority_label", "low")] + list(entities.get("actions", []))[:2],
        "sources": [
            {
                "file": file_name,
                "events": total_rows,
                "hits": len(evidence_bundle),
                "primary": True,
                "description": "Correlated directly from the uploaded package through live normalization, prefiltering, anomaly scoring, and prioritization.",
            }
        ],
        "evidence": _incident_evidence(priority_record),
        "riskBreakdown": _risk_breakdown(priority_record),
        "confidenceReasons": priority_record.get("reasons", [])[:4] or ["Calculated from the uploaded file's correlated evidence."],
        "stages": _incident_stages(priority_record),
        "impact": [
            {"label": "Priority", "value": priority_record.get("priority_label", "low").title(), "tone": "danger" if severity == "critical" else "warning"},
            {"label": "Related events", "value": str(len(evidence_bundle)), "tone": "neutral"},
            {"label": "LLM eligible", "value": "Yes" if priority_record.get("llm_eligible") else "No", "tone": "neutral"},
            {"label": "Source file", "value": file_name, "tone": "neutral"},
        ],
        "actions": _incident_actions(priority_record, file_name),
        "logs": [_event_log_line(evidence) for evidence in evidence_bundle[:10]],
    }


def build_live_ingestion_payload(path: Path, dataset_id: str, domain: str, limit: int = 50) -> dict[str, Any]:
    prefilter = PrefilteringPipeline.load_from_artifacts(_resolve_prefilter_dir())
    entity_model = EntityAnomalyEnsemble.load(_resolve_entity_model())

    rows = []
    canonical_events: list[dict[str, Any]] = []
    terminal_lines = [
        "[SYSTEM] Initializing intake stream...",
        f"> Loading {path.name} [OK]",
    ]
    label_counter: Counter[str] = Counter()

    raw_records = list(load_records(path))
    for index, raw_record in enumerate(raw_records[:limit], start=1):
        canonical_event = _canonical_row(raw_record, path, dataset_id, domain, index)
        model_row = _model_row(canonical_event)
        prefilter_result = prefilter.evaluate("cyber_threat_logs_v1", canonical_event, model_row)
        anomaly_result = score_entity_behavior(entity_model.score_event(canonical_event)).to_dict()

        canonical_event["labels"]["prefilter_label"] = prefilter_result.final_label
        canonical_event["labels"]["anomaly_label"] = anomaly_result.get("label")
        canonical_event["anomaly"] = anomaly_result
        canonical_event["confidence"] = round(float(prefilter_result.final_score), 4)
        canonical_events.append(canonical_event)

        label_counter[prefilter_result.final_label] += 1
        source_name = canonical_event.get("source", {}).get("source_type") or canonical_event.get("event_kind") or "unknown"
        status = canonical_event.get("artifacts", {}).get("action") or canonical_event.get("event_kind") or "Observed"

        rows.append(
            {
                "id": canonical_event["event_id"],
                "source": str(source_name),
                "status": str(status),
                "classification": _classification_label(prefilter_result.final_label),
                "confidence": int(round(prefilter_result.final_score * 100)),
                "anomalyScore": int(round(float(anomaly_result["final_score"]) * 100)),
                "severity": canonical_event.get("severity", "unknown"),
            }
        )

    terminal_lines.append(f"> Normalizing logs... {min(limit, len(raw_records))}/{len(raw_records)}")
    if rows:
        top_row = max(rows, key=lambda item: (item["confidence"], item["anomalyScore"]))
        terminal_lines.append(f"> Top pattern: {top_row['status']} [{top_row['classification']}]")
        terminal_lines.append("> Applied prefilter policy: TrustSphere_live")
    else:
        terminal_lines.append("> No records parsed from the selected file")

    evaluated = sum(label_counter.values()) or 1
    true_positive = label_counter.get("true_positive", 0)
    false_positive = label_counter.get("false_positive", 0)
    uncertain = label_counter.get("uncertain", 0)
    noise_removed = int(round((false_positive / evaluated) * 100))

    incidents = build_incidents(canonical_events)
    priority_records = prioritize_incidents(
        incidents,
        asset_context_path=ASSET_CONTEXT_PATH,
        feedback_path=None,
    )
    terminal_incidents = [
        _serialize_priority_record(record, path.name, len(raw_records))
        for record in priority_records
    ]
    terminal_lines.append(f"> Correlated incidents: {len(priority_records)}")

    return {
        "fileName": path.name,
        "datasetId": dataset_id,
        "domain": domain,
        "stats": [
            {
                "label": "True Positives",
                "value": f"{true_positive:02d}",
                "accent": "var(--primary)",
                "note": "Live ML prefilter output",
                "icon": "verified_user",
            },
            {
                "label": "False Positives",
                "value": f"{false_positive:02d}",
                "accent": "var(--error)",
                "note": "Suppressed by prefiltering",
                "icon": "gpp_maybe",
            },
            {
                "label": "Uncertain",
                "value": f"{uncertain:02d}",
                "accent": "var(--tertiary-container)",
                "note": "Needs analyst review",
                "icon": "help_outline",
            },
            {
                "label": "Noise Removed",
                "value": f"{noise_removed}%",
                "accent": "var(--secondary)",
                "note": "Estimated from current batch",
                "icon": "filter_alt",
            },
        ],
        "rows": rows,
        "terminal": terminal_lines,
        "incidents": terminal_incidents,
    }


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/frontend_live_ingestion.py <input_path> <dataset_id> <domain> [limit]")
        raise SystemExit(1)

    payload = build_live_ingestion_payload(
        Path(sys.argv[1]),
        sys.argv[2],
        sys.argv[3],
        int(sys.argv[4]) if len(sys.argv) > 4 else 50,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
