from __future__ import annotations

import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anomaly_detection.models.behavioral_anomaly_model import BehavioralAnomalyDetector
from prefiltering.ml.labels import map_dataset_label
from prefiltering.ml.supervised_model import StreamingEventClassifier
from shared.types.dataset_registry import registry_by_id


ARTIFACT_DIR = ROOT / "artifacts" / "prefiltering"
REGISTRY_PATH = ROOT / "configs" / "dataset_registry.json"


def iter_csv(path: str) -> Iterator[dict[str, Any]]:
    csv.field_size_limit(10_000_000)
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield dict(row)


def iter_zip_csv(zip_path: str, member: str) -> Iterator[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as raw:
            csv.field_size_limit(10_000_000)
            reader = csv.DictReader(line.decode("utf-8", errors="ignore") for line in raw)
            for row in reader:
                yield dict(row)


def stream_rows(dataset_spec) -> Iterator[dict[str, Any]]:
    if dataset_spec.source_type == "file" and dataset_spec.format == "csv":
        yield from iter_csv(dataset_spec.path)
        return
    if dataset_spec.source_type == "archive_member" and dataset_spec.format == "csv":
        yield from iter_zip_csv(dataset_spec.path, dataset_spec.archive_member)
        return
    raise ValueError(f"Unsupported training dataset source: {dataset_spec.id}")


def train_primary_classifier(dataset_spec, max_rows: int | None = None, batch_size: int = 5000) -> dict[str, Any]:
    classifier = StreamingEventClassifier()
    classifier.set_dataset(dataset_spec.id)

    eval_rows: list[dict[str, Any]] = []
    eval_labels: list[str] = []
    anomaly_training_rows: list[dict[str, Any]] = []
    balanced_buffers: dict[str, list[dict[str, Any]]] = {
        "false_positive": [],
        "uncertain": [],
        "true_positive": [],
    }
    seen = 0

    balanced_chunk = max(256, batch_size // 3)
    buffer_cap = balanced_chunk * 4

    for row in stream_rows(dataset_spec):
        mapped = map_dataset_label(dataset_spec.id, row.get(dataset_spec.label_field))
        if mapped is None:
            continue
        seen += 1
        bucket = seen % 10
        if bucket == 0:
            eval_rows.append(row)
            eval_labels.append(mapped)
        else:
            balanced_buffers[mapped].append(row)
            if len(balanced_buffers[mapped]) > buffer_cap:
                del balanced_buffers[mapped][: len(balanced_buffers[mapped]) - buffer_cap]
            if mapped == "false_positive" and len(anomaly_training_rows) < 120000:
                anomaly_training_rows.append(row)

        if all(len(buffer) >= balanced_chunk for buffer in balanced_buffers.values()):
            train_rows: list[dict[str, Any]] = []
            train_labels: list[str] = []
            for label_name, buffer in balanced_buffers.items():
                train_rows.extend(buffer[:balanced_chunk])
                train_labels.extend([label_name] * balanced_chunk)
                del buffer[:balanced_chunk]
            classifier.partial_fit(train_rows, train_labels)

        if max_rows and seen >= max_rows:
            break

    remaining_rows: list[dict[str, Any]] = []
    remaining_labels: list[str] = []
    remaining_per_label = min(len(buffer) for buffer in balanced_buffers.values() if buffer)
    if remaining_per_label:
        for label_name, buffer in balanced_buffers.items():
            remaining_rows.extend(buffer[:remaining_per_label])
            remaining_labels.extend([label_name] * remaining_per_label)
    if remaining_rows:
        classifier.partial_fit(remaining_rows, remaining_labels)

    predictions = Counter()
    expected_distribution = Counter(eval_labels)
    correct = 0
    for row, expected in zip(eval_rows, eval_labels):
        predicted = classifier.predict(dataset_spec.id, row).label
        predictions[predicted] += 1
        if predicted == expected:
            correct += 1

    anomaly = BehavioralAnomalyDetector()
    anomaly.fit(dataset_spec.id, anomaly_training_rows[:50000] if anomaly_training_rows else eval_rows[:1000])

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    classifier.save(ARTIFACT_DIR / "prefilter_primary.joblib")
    anomaly.save(ARTIFACT_DIR / "prefilter_anomaly.joblib")

    metrics = {
        "trained_rows": seen,
        "evaluation_rows": len(eval_rows),
        "evaluation_accuracy": round(correct / len(eval_rows), 4) if eval_rows else 0.0,
        "evaluation_expected_distribution": dict(expected_distribution),
        "prediction_distribution": dict(predictions),
        "anomaly_reference_rows": len(anomaly_training_rows),
    }
    return metrics


def train_auxiliary_classifier(dataset_spec, artifact_name: str, max_rows: int | None = None) -> dict[str, Any]:
    classifier = StreamingEventClassifier()
    classifier.set_dataset(dataset_spec.id)
    rows: list[dict[str, Any]] = []
    labels: list[str] = []
    seen = 0

    for row in stream_rows(dataset_spec):
        mapped = map_dataset_label(dataset_spec.id, row.get(dataset_spec.label_field))
        if mapped is None:
            continue
        rows.append(row)
        labels.append(mapped)
        seen += 1
        if len(rows) >= 5000:
            classifier.partial_fit(rows, labels)
            rows, labels = [], []
        if max_rows and seen >= max_rows:
            break

    if rows:
        classifier.partial_fit(rows, labels)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    classifier.save(ARTIFACT_DIR / artifact_name)
    return {"trained_rows": seen}


def main() -> None:
    max_rows = int(sys.argv[1]) if len(sys.argv) > 1 else None
    registry = registry_by_id(REGISTRY_PATH)

    summary = {
        "primary": train_primary_classifier(registry["cyber_threat_logs_v1"], max_rows=max_rows),
        "auxiliary_email": train_auxiliary_classifier(registry["email_text_v1"], "prefilter_email_aux.joblib", max_rows=15000),
        "auxiliary_phishing": train_auxiliary_classifier(registry["website_phishing_v1"], "prefilter_phishing_aux.joblib", max_rows=None),
    }

    (ARTIFACT_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
