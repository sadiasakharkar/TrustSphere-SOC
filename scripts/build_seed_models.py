from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anomaly_detection.models.behavioral_anomaly_model import BehavioralAnomalyDetector
from anomaly_detection.models.entity_anomaly_ensemble import EntityAnomalyEnsemble
from ingestion.adapters.normalize_records import ingest_and_normalize
from ingestion.loaders.file_loader import load_records
from prefiltering.ml.labels import map_dataset_label
from prefiltering.ml.supervised_model import StreamingEventClassifier


SEED_ROOT = ROOT / "seed_models"
PREFILTER_ROOT = SEED_ROOT / "prefiltering"
ANOMALY_ROOT = SEED_ROOT / "anomaly_detection"


def _csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _fixture_rows() -> list[dict]:
    rows: list[dict] = []

    for row in _csv_rows(ROOT / "tests" / "fixtures" / "sample_events.csv"):
        rows.append(row)

    for record in load_records(ROOT / "tests" / "fixtures" / "sample_events.json"):
        label = record.get("classification") or record.get("threat_label")
        rows.append(
            {
                "source_ip": record.get("src_ip"),
                "src_ip": record.get("src_ip"),
                "dest_ip": record.get("destination_ip"),
                "destination_ip": record.get("destination_ip"),
                "protocol": record.get("proto"),
                "proto": record.get("proto"),
                "action": record.get("decision"),
                "decision": record.get("decision"),
                "threat_label": label,
                "classification": label,
                "log_type": record.get("event_category"),
                "event_category": record.get("event_category"),
                "bytes_transferred": record.get("bytes_out"),
                "bytes_out": record.get("bytes_out"),
                "user_agent": record.get("ua"),
                "ua": record.get("ua"),
                "request_path": record.get("uri"),
                "uri": record.get("uri"),
            }
        )

    for record in load_records(ROOT / "tests" / "fixtures" / "sample_events.syslog"):
        label = record.get("classification") or record.get("threat_label")
        rows.append(
            {
                "source_ip": record.get("src_ip"),
                "src_ip": record.get("src_ip"),
                "dest_ip": record.get("destination_ip"),
                "destination_ip": record.get("destination_ip"),
                "protocol": record.get("proto"),
                "proto": record.get("proto"),
                "action": record.get("decision"),
                "decision": record.get("decision"),
                "threat_label": label,
                "classification": label,
                "log_type": record.get("event_category"),
                "event_category": record.get("event_category"),
                "bytes_transferred": record.get("bytes_out"),
                "bytes_out": record.get("bytes_out"),
                "user_agent": record.get("ua"),
                "ua": record.get("ua"),
                "request_path": record.get("uri"),
                "uri": record.get("uri"),
            }
        )

    return rows


def _normalized_events() -> list[dict]:
    events: list[dict] = []
    for fixture in ("sample_events.csv", "sample_events.json", "sample_events.syslog"):
        events.extend(
            ingest_and_normalize(
                ROOT / "tests" / "fixtures" / fixture,
                dataset_id="frontend_seed",
                domain="network",
                source_type="file",
            )
        )
    return events


def build_prefilter_models(rows: list[dict]) -> None:
    classifier = StreamingEventClassifier(n_features=2**12)
    classifier.set_dataset("cyber_threat_logs_v1")

    train_rows: list[dict] = []
    labels: list[str] = []
    for row in rows:
        raw_label = row.get("threat_label") or row.get("classification")
        mapped = map_dataset_label("cyber_threat_logs_v1", raw_label)
        if mapped is None:
            continue
        train_rows.append(row)
        labels.append(mapped)

    classifier.partial_fit(train_rows, labels)

    anomaly_detector = BehavioralAnomalyDetector(n_features=2**10, n_estimators=20)
    benign_rows = [row for row in train_rows if map_dataset_label("cyber_threat_logs_v1", row.get("threat_label") or row.get("classification")) == "false_positive"]
    anomaly_detector.fit("cyber_threat_logs_v1", benign_rows or train_rows)

    PREFILTER_ROOT.mkdir(parents=True, exist_ok=True)
    classifier.save(PREFILTER_ROOT / "prefilter_primary.joblib")
    anomaly_detector.save(PREFILTER_ROOT / "prefilter_anomaly.joblib")


def build_entity_model(events: list[dict]) -> None:
    model = EntityAnomalyEnsemble(n_features=2**11, n_estimators=24)
    benign_events = [event for event in events if event.get("labels", {}).get("ground_truth") in {None, "benign"}]
    model.fit(benign_events or events)

    ANOMALY_ROOT.mkdir(parents=True, exist_ok=True)
    model.save(ANOMALY_ROOT / "entity_anomaly_ensemble.joblib")


def main() -> None:
    rows = _fixture_rows()
    events = _normalized_events()
    build_prefilter_models(rows)
    build_entity_model(events)
    print("Seed models created in seed_models/")


if __name__ == "__main__":
    main()
