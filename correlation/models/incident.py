from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class EvidenceItem:
    event_id: str
    event_time: str
    event_kind: str
    severity: str
    confidence: float
    principal: dict[str, Any]
    artifacts: dict[str, Any]
    labels: dict[str, Any]
    anomaly: dict[str, Any] | None = None
    raw_ref: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IncidentRecord:
    incident_id: str
    incident_type: str
    status: str
    severity: str
    confidence: float
    start_time: str
    end_time: str
    entities: dict[str, list[str]]
    timeline: list[dict[str, Any]] = field(default_factory=list)
    evidence_bundle: list[dict[str, Any]] = field(default_factory=list)
    related_event_ids: list[str] = field(default_factory=list)
    merged_duplicates: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
