from __future__ import annotations

import hashlib
from typing import Any


def normalized_value(value: Any) -> str:
    return str(value or "").strip().lower()


def build_dedup_signature(event: dict[str, Any]) -> str:
    principal = event.get("principal", {})
    artifacts = event.get("artifacts", {})
    parts = [
        normalized_value(event.get("event_kind")),
        normalized_value(principal.get("src_ip")),
        normalized_value(principal.get("dest_ip")),
        normalized_value(principal.get("user_id")),
        normalized_value(principal.get("email")),
        normalized_value(artifacts.get("protocol")),
        normalized_value(artifacts.get("action")),
        normalized_value(artifacts.get("request_path")),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()


def build_incident_key(event: dict[str, Any]) -> str:
    principal = event.get("principal", {})
    parts = [
        normalized_value(principal.get("src_ip")),
        normalized_value(principal.get("dest_ip")),
        normalized_value(principal.get("user_id") or principal.get("email")),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:20]
