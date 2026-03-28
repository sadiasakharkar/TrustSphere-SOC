from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DatasetSpec:
    id: str
    display_name: str
    source_type: str
    path: str
    format: str
    domain: str
    role: str
    tasks: list[str]
    enabled: bool = True
    archive_member: str | None = None
    label_field: str | None = None
    text_fields: list[str] | None = None
    timestamp_field: str | None = None
    expected_fields: list[str] | None = None
    split_strategy: str | None = None
    duplicate_of: str | None = None


def load_dataset_registry(path: str | Path) -> list[DatasetSpec]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [DatasetSpec(**item) for item in payload["datasets"]]


def registry_by_id(path: str | Path) -> dict[str, DatasetSpec]:
    return {spec.id: spec for spec in load_dataset_registry(path)}
