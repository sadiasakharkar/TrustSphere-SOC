from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class EventSource:
    dataset_id: str
    source_type: str
    collector: str | None = None
    host: str | None = None


@dataclass(slots=True)
class EventPrincipal:
    user_id: str | None = None
    email: str | None = None
    src_ip: str | None = None
    dest_ip: str | None = None
    hostname: str | None = None


@dataclass(slots=True)
class EventArtifacts:
    protocol: str | None = None
    action: str | None = None
    request_path: str | None = None
    user_agent: str | None = None
    bytes_transferred: int | None = None
    urls: list[str] = field(default_factory=list)
    subject: str | None = None
    body: str | None = None
    feature_map: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EventLabels:
    ground_truth: str | None = None
    prefilter_label: str | None = None
    anomaly_label: str | None = None


@dataclass(slots=True)
class RawReference:
    dataset_path: str
    archive_member: str | None = None
    row_number: int | None = None
    content_hash: str | None = None


@dataclass(slots=True)
class CanonicalSecurityEvent:
    event_id: str
    event_time: str
    source: EventSource
    raw_format: str
    event_kind: str
    severity: str
    confidence: float
    artifacts: EventArtifacts
    labels: EventLabels
    raw_ref: RawReference
    ingest_time: str = field(default_factory=utc_now_iso)
    principal: EventPrincipal = field(default_factory=EventPrincipal)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
