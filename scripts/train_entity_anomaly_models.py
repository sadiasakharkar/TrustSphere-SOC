from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anomaly_detection.models.entity_anomaly_ensemble import EntityAnomalyEnsemble
from ingestion.adapters.normalize_records import ingest_and_normalize
from shared.types.dataset_registry import registry_by_id


ARTIFACT_DIR = ROOT / "artifacts" / "anomaly_detection"
REGISTRY_PATH = ROOT / "configs" / "dataset_registry.json"


def load_normalized_events(dataset_spec, limit: int | None = None, benign_only: bool = False) -> list[dict]:
    events: list[dict] = []
    iterator = ingest_and_normalize(
        dataset_spec.path,
        dataset_id=dataset_spec.id,
        domain=dataset_spec.domain,
        source_type=dataset_spec.source_type,
        archive_member=dataset_spec.archive_member,
    )
    for event in iterator:
        if benign_only and event.get("labels", {}).get("ground_truth") not in {None, "benign"}:
            continue
        events.append(event)
        if limit and len(events) >= limit:
            break
    return events


def load_threat_events(dataset_spec, limit: int | None = None) -> list[dict]:
    events: list[dict] = []
    iterator = ingest_and_normalize(
        dataset_spec.path,
        dataset_id=dataset_spec.id,
        domain=dataset_spec.domain,
        source_type=dataset_spec.source_type,
        archive_member=dataset_spec.archive_member,
    )
    for event in iterator:
        label = event.get("labels", {}).get("ground_truth")
        if label not in {"suspicious", "malicious"}:
            continue
        events.append(event)
        if limit and len(events) >= limit:
            break
    return events


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    benign_only = (sys.argv[2].lower() == "true") if len(sys.argv) > 2 else True

    registry = registry_by_id(REGISTRY_PATH)
    dataset_spec = registry["cyber_threat_logs_v1"]
    events = load_normalized_events(dataset_spec, limit=limit, benign_only=benign_only)
    mixed_eval_events = load_normalized_events(dataset_spec, limit=min(25000, max(limit // 4, 5000)), benign_only=False)
    threat_eval_events = load_threat_events(dataset_spec, limit=min(5000, max(limit // 8, 1000)))

    train_cutoff = int(len(events) * 0.8)
    train_events = events[:train_cutoff]
    eval_events = mixed_eval_events if benign_only else events[train_cutoff:]

    model = EntityAnomalyEnsemble()
    model.fit(train_events)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model.save(ARTIFACT_DIR / "entity_anomaly_ensemble.joblib")

    scores = [model.score_event(event) for event in eval_events[: min(len(eval_events), 5000)]]
    average_score = sum(float(item["final_score"]) for item in scores) / len(scores) if scores else 0.0
    anomalous_count = sum(1 for item in scores if item["label"] == "anomalous")
    threat_scores = [model.score_event(event) for event in threat_eval_events]
    threat_average = sum(float(item["final_score"]) for item in threat_scores) / len(threat_scores) if threat_scores else 0.0
    threat_anomalous_count = sum(1 for item in threat_scores if item["label"] == "anomalous")
    summary = {
        "trained_events": len(train_events),
        "evaluated_events": len(scores),
        "benign_only_training": benign_only,
        "average_final_score": round(average_score, 4),
        "anomalous_eval_events": anomalous_count,
        "threat_eval_events": len(threat_scores),
        "threat_average_final_score": round(threat_average, 4),
        "threat_anomalous_events": threat_anomalous_count,
    }
    (ARTIFACT_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
