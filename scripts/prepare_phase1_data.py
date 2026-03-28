from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.types.dataset_registry import DatasetSpec, load_dataset_registry

REGISTRY_PATH = ROOT / "configs" / "dataset_registry.json"
PROCESSED_DIR = ROOT / "datasets" / "processed"

SPLIT_BUCKETS = {
    "train": range(0, 80),
    "validation": range(80, 90),
    "test": range(90, 100),
}


def ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def split_name_from_hash(hash_value: str) -> str:
    bucket = int(hash_value[:8], 16) % 100
    for name, rng in SPLIT_BUCKETS.items():
        if bucket in rng:
            return name
    return "train"


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def fingerprint_row(row: dict[str, str], preferred_fields: Iterable[str]) -> str:
    parts: list[str] = []
    for field in preferred_fields:
        if field in row and row[field] is not None:
            parts.append(normalize_text(str(row[field])))
    if not parts:
        for key in sorted(row):
            value = row[key]
            if value:
                parts.append(f"{key}={normalize_text(str(value))}")
    return stable_hash("|".join(parts))


def iter_csv_rows(spec: DatasetSpec) -> Iterator[dict[str, str]]:
    if spec.source_type == "file":
        with open(spec.path, "r", newline="", encoding="utf-8") as f:
            csv.field_size_limit(1_000_000)
            reader = csv.DictReader(f)
            for row in reader:
                yield row
        return

    if spec.source_type == "archive_member":
        with zipfile.ZipFile(spec.path) as archive:
            with archive.open(spec.archive_member or "") as raw:
                csv.field_size_limit(10_000_000)
                text_stream = (line.decode("utf-8", errors="ignore") for line in raw)
                reader = csv.DictReader(text_stream)
                for row in reader:
                    yield row
        return

    raise ValueError(f"Unsupported CSV source type: {spec.source_type}")


def iter_arff_rows(spec: DatasetSpec) -> Iterator[list[str]]:
    with zipfile.ZipFile(spec.path) as archive:
        with archive.open(spec.archive_member or "") as raw:
            in_data = False
            for line in raw:
                text = line.decode("utf-8", errors="ignore").strip()
                if not text or text.startswith("%"):
                    continue
                if text.lower() == "@data":
                    in_data = True
                    continue
                if in_data:
                    yield [part.strip() for part in text.split(",")]


def clear_previous_outputs(dataset_id: str) -> None:
    for pattern in (f"{dataset_id}_*.json", f"{dataset_id}_*.jsonl"):
        for path in PROCESSED_DIR.glob(pattern):
            path.unlink()


def blank_split_summary() -> dict[str, dict[str, object]]:
    return {
        split: {
            "row_count": 0,
            "label_distribution": {},
            "sample_rows": [],
            "sample_fingerprints": [],
        }
        for split in SPLIT_BUCKETS
    }


def update_split_summary(
    split_summary: dict[str, dict[str, object]],
    split: str,
    row_number: int,
    label: str | None,
    fingerprint: str,
    row: object,
) -> None:
    entry = split_summary[split]
    entry["row_count"] += 1
    if label not in (None, ""):
        label_distribution = entry["label_distribution"]
        label_distribution[str(label)] = label_distribution.get(str(label), 0) + 1
    if len(entry["sample_fingerprints"]) < 5:
        entry["sample_fingerprints"].append(fingerprint)
    if len(entry["sample_rows"]) < 3:
        entry["sample_rows"].append(
            {
                "row_number": row_number,
                "label": label,
                "fingerprint": fingerprint,
                "data": row,
            }
        )


def write_split_summary(dataset_id: str, split_summary: dict[str, dict[str, object]]) -> None:
    summary_path = PROCESSED_DIR / f"{dataset_id}_splits.json"
    summary_path.write_text(json.dumps(split_summary, indent=2), encoding="utf-8")


def prepare_csv_dataset(spec: DatasetSpec) -> dict[str, object]:
    clear_previous_outputs(spec.id)
    labels = Counter()
    row_count = 0
    field_names: set[str] = set()
    sample_hashes: list[str] = []
    split_summary = blank_split_summary()

    preferred_fields = []
    if spec.text_fields:
        preferred_fields.extend(spec.text_fields)
    if spec.timestamp_field:
        preferred_fields.append(spec.timestamp_field)
    if spec.expected_fields:
        preferred_fields.extend(spec.expected_fields)

    for index, row in enumerate(iter_csv_rows(spec), start=1):
        row_count += 1
        field_names.update(row.keys())
        label = row.get(spec.label_field) if spec.label_field else None
        if label not in (None, ""):
            labels[str(label)] += 1

        row_hash = fingerprint_row(row, preferred_fields)
        if len(sample_hashes) < 5:
            sample_hashes.append(row_hash)

        split = split_name_from_hash(row_hash)
        update_split_summary(split_summary, split, index, label, row_hash, row)

    write_split_summary(spec.id, split_summary)

    return {
        "dataset_id": spec.id,
        "display_name": spec.display_name,
        "format": spec.format,
        "source_type": spec.source_type,
        "path": spec.path,
        "archive_member": spec.archive_member,
        "row_count": row_count,
        "field_names": sorted(field_names),
        "label_distribution": dict(labels),
        "sample_fingerprints": sample_hashes,
        "split_summary_file": f"{spec.id}_splits.json",
    }


def prepare_archive_catalog(spec: DatasetSpec) -> dict[str, object]:
    with zipfile.ZipFile(spec.path) as archive:
        members = []
        for member in archive.infolist():
            members.append(
                {
                    "name": member.filename,
                    "file_size": member.file_size,
                    "compressed_size": member.compress_size,
                }
            )
    return {
        "dataset_id": spec.id,
        "display_name": spec.display_name,
        "format": spec.format,
        "source_type": spec.source_type,
        "path": spec.path,
        "members": members,
    }


def prepare_arff_dataset(spec: DatasetSpec) -> dict[str, object]:
    clear_previous_outputs(spec.id)
    labels = Counter()
    row_count = 0
    sample_hashes: list[str] = []
    split_summary = blank_split_summary()

    for index, row in enumerate(iter_arff_rows(spec), start=1):
        row_count += 1
        row_hash = stable_hash("|".join(row))
        if len(sample_hashes) < 5:
            sample_hashes.append(row_hash)
        split = split_name_from_hash(row_hash)
        label = row[-1] if row else None
        if label not in (None, ""):
            labels[str(label)] += 1
        update_split_summary(split_summary, split, index, label, row_hash, row)

    write_split_summary(spec.id, split_summary)

    return {
        "dataset_id": spec.id,
        "display_name": spec.display_name,
        "format": spec.format,
        "source_type": spec.source_type,
        "path": spec.path,
        "archive_member": spec.archive_member,
        "row_count": row_count,
        "label_distribution": dict(labels),
        "sample_fingerprints": sample_hashes,
        "split_summary_file": f"{spec.id}_splits.json",
    }


def prepare_dataset(spec: DatasetSpec) -> dict[str, object]:
    if spec.format == "zip":
        return prepare_archive_catalog(spec)
    if spec.format == "csv":
        return prepare_csv_dataset(spec)
    if spec.format == "arff":
        return prepare_arff_dataset(spec)
    raise ValueError(f"Unsupported format: {spec.format}")


def main() -> None:
    ensure_dirs()
    registry = load_dataset_registry(REGISTRY_PATH)
    manifests = []
    for spec in registry:
        if not spec.enabled:
            continue
        manifests.append(prepare_dataset(spec))

    manifest_path = PROCESSED_DIR / "phase1_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "phase": "phase1_data_foundation",
                "dataset_count": len(manifests),
                "manifests": manifests,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
