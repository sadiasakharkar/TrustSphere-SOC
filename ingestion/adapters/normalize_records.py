from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from ingestion.loaders.file_loader import load_records
from normalization.mappers.canonical_mapper import canonicalize_record
from normalization.validators.canonical_validator import validate_canonical_event


def ingest_and_normalize(
    path: str | Path,
    *,
    dataset_id: str,
    domain: str,
    source_type: str = "file",
    archive_member: str | None = None,
) -> Iterator[dict[str, Any]]:
    resolved = Path(path)
    raw_format = resolved.suffix.lower().lstrip(".") or "unknown"
    for row_number, record in enumerate(load_records(resolved), start=1):
        event = canonicalize_record(
            record,
            dataset_id=dataset_id,
            dataset_path=str(resolved),
            source_type=source_type,
            domain=domain,
            raw_format=raw_format,
            archive_member=archive_member,
            row_number=row_number,
        )
        payload = event.to_dict()
        errors = validate_canonical_event(payload)
        if errors:
            payload["normalization_errors"] = errors
        yield payload
