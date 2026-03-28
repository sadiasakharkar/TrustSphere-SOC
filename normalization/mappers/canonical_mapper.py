from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from typing import Any

from normalization.mappers.field_aliases import FIELD_ALIASES
from shared.types.canonical_schema import (
    CanonicalSecurityEvent,
    EventArtifacts,
    EventLabels,
    EventPrincipal,
    EventSource,
    RawReference,
)


SEVERITY_MAP = {
    "malicious": "critical",
    "suspicious": "high",
    "benign": "low",
    "1": "high",
    "0": "low",
    "-1": "medium",
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "atrisk": "high",
    "none": "low",
}

EVENT_KIND_MAP = {
    "firewall": "network",
    "ids": "alert",
    "application": "application",
    "email_security": "email",
    "url_security": "url",
    "network_security": "network",
    "phishing_bundle": "alert",
    "azure_ad": "identity",
    "office365": "email",
    "windows_security": "identity",
    "sysmon": "endpoint",
    "zeek": "network",
    "cloud_waf": "application",
    "github_actions_runner": "application",
}


def _first_value(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in record and record[alias] not in (None, ""):
            return record[alias]
    return None


def _normalize_timestamp(value: Any) -> str:
    if value in (None, ""):
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    text = str(value).strip()
    for parser in (
        lambda candidate: datetime.fromisoformat(candidate.replace("Z", "+00:00")),
        lambda candidate: datetime.strptime(candidate, "%a, %d %b %Y %H:%M:%S %z"),
        lambda candidate: datetime.strptime(candidate, "%b %d %H:%M:%S"),
        lambda candidate: datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S"),
    ):
        try:
            parsed = parser(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(year=datetime.now().year, tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value)))
    except ValueError:
        return None


def _normalize_urls(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]

    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except (ValueError, SyntaxError):
            pass
    if "http" in text and "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]


def _derive_event_kind(domain: str, record: dict[str, Any], log_type: str | None) -> str:
    if log_type and log_type in EVENT_KIND_MAP:
        return EVENT_KIND_MAP[log_type]
    return EVENT_KIND_MAP.get(domain, "unknown")


def _derive_confidence(label: str | None) -> float:
    normalized = str(label or "").strip().lower()
    if normalized == "malicious":
        return 0.95
    if normalized == "suspicious":
        return 0.75
    if normalized == "benign":
        return 0.2
    if normalized == "1":
        return 0.8
    if normalized == "0":
        return 0.2
    if normalized == "-1":
        return 0.5
    if normalized == "critical":
        return 0.95
    if normalized == "high":
        return 0.8
    if normalized == "medium":
        return 0.6
    if normalized == "low":
        return 0.3
    if normalized == "atrisk":
        return 0.8
    return 0.5


def _derive_source_type(record: dict[str, Any], default: str) -> str:
    for key in ("source", "log_source", "source_type", "event_category"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _infer_action(record: dict[str, Any], known_action: Any) -> str | None:
    if known_action not in (None, ""):
        return str(known_action)
    event_id = str(record.get("EventID") or "")
    if event_id == "4624":
        return "login_success"
    if event_id == "4625":
        return "login_failure"
    if event_id == "1":
        return "process_create"
    if event_id == "10":
        return "process_access"
    return None


def _infer_request_path(record: dict[str, Any], known_path: Any) -> str | None:
    if known_path not in (None, ""):
        return str(known_path)
    for key in ("http_uri", "QueryName", "file"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def canonicalize_record(
    record: dict[str, Any],
    *,
    dataset_id: str,
    dataset_path: str,
    source_type: str,
    domain: str,
    raw_format: str,
    archive_member: str | None = None,
    row_number: int | None = None,
) -> CanonicalSecurityEvent:
    timestamp = _normalize_timestamp(_first_value(record, FIELD_ALIASES["timestamp"]))
    threat_label = _first_value(record, FIELD_ALIASES["threat_label"])
    log_type = _first_value(record, FIELD_ALIASES["log_type"])
    payload_hash = hashlib.sha256(repr(sorted(record.items())).encode("utf-8", errors="ignore")).hexdigest()

    known_values = {
        canonical_name: _first_value(record, aliases)
        for canonical_name, aliases in FIELD_ALIASES.items()
    }
    known_values["log_type"] = _derive_source_type(record, str(log_type) if log_type else source_type)
    known_values["action"] = _infer_action(record, known_values["action"])
    known_values["request_path"] = _infer_request_path(record, known_values["request_path"])
    feature_map = {
        key: value
        for key, value in record.items()
        if key not in {alias for aliases in FIELD_ALIASES.values() for alias in aliases}
    }

    principal = EventPrincipal(
        user_id=_first_value(record, FIELD_ALIASES["user_id"]),
        email=_first_value(record, FIELD_ALIASES["email"]),
        src_ip=_first_value(record, FIELD_ALIASES["source_ip"]),
        dest_ip=_first_value(record, FIELD_ALIASES["dest_ip"]),
        hostname=_first_value(record, FIELD_ALIASES["host"]),
    )
    artifacts = EventArtifacts(
        protocol=known_values["protocol"],
        action=known_values["action"],
        request_path=known_values["request_path"],
        user_agent=known_values["user_agent"],
        bytes_transferred=_normalize_int(known_values["bytes_transferred"]),
        urls=_normalize_urls(known_values["urls"]),
        subject=known_values["subject"],
        body=known_values["body"],
        feature_map=feature_map,
    )
    labels = EventLabels(ground_truth=str(threat_label) if threat_label is not None else None)
    source = EventSource(dataset_id=dataset_id, source_type=known_values["log_type"], host=known_values["host"])
    raw_ref = RawReference(
        dataset_path=dataset_path,
        archive_member=archive_member,
        row_number=row_number,
        content_hash=payload_hash,
    )
    event_id = f"{dataset_id}:{row_number or payload_hash[:12]}"

    return CanonicalSecurityEvent(
        event_id=event_id,
        event_time=timestamp,
        source=source,
        raw_format=raw_format,
        event_kind=_derive_event_kind(domain, record, str(known_values["log_type"]) if known_values["log_type"] else None),
        severity=SEVERITY_MAP.get(str(threat_label).strip().lower(), "unknown"),
        confidence=_derive_confidence(str(threat_label) if threat_label is not None else None),
        principal=principal,
        artifacts=artifacts,
        labels=labels,
        raw_ref=raw_ref,
    )
