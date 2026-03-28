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
from ingestion.loaders.file_loader import load_records
from normalization.mappers.canonical_mapper import canonicalize_record
from normalization.validators.canonical_validator import validate_canonical_event
from prefiltering.pipeline import PrefilteringPipeline


ARTIFACT_PREFILTER = ROOT / "artifacts" / "prefiltering"
ARTIFACT_ANOMALY = ROOT / "artifacts" / "anomaly_detection" / "entity_anomaly_ensemble.joblib"


def _classification_label(label: str) -> str:
    mapping = {
        "true_positive": "True Positive",
        "false_positive": "False Positive",
        "uncertain": "Uncertain",
    }
    return mapping.get(label, "Uncertain")


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


def build_live_ingestion_payload(path: Path, dataset_id: str, domain: str, limit: int = 50) -> dict[str, Any]:
    prefilter = PrefilteringPipeline.load_from_artifacts(ARTIFACT_PREFILTER)
    entity_model = EntityAnomalyEnsemble.load(ARTIFACT_ANOMALY)

    rows = []
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
        canonical_event["anomaly"] = anomaly_result

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
