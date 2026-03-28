from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from ipaddress import ip_address, ip_network
from math import log1p
from typing import Any


INTERNAL_NETWORKS = (
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
)


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _is_internal(ip_value: str) -> bool:
    try:
        candidate = ip_address(ip_value)
    except ValueError:
        return False
    return any(candidate in network for network in INTERNAL_NETWORKS)


def _parse_event_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _user_agent_family(user_agent: str) -> str:
    text = user_agent.lower()
    if "nmap" in text:
        return "scanner"
    if "curl" in text or "python-requests" in text or "wget" in text:
        return "automation"
    if "mozilla" in text:
        return "browser"
    return "other"


def build_entity_keys(event: dict[str, Any]) -> dict[str, str]:
    principal = event.get("principal", {})
    artifacts = event.get("artifacts", {})
    keys = {
        "user": _safe_str(principal.get("user_id") or principal.get("email")),
        "src_ip": _safe_str(principal.get("src_ip")),
        "dest_ip": _safe_str(principal.get("dest_ip")),
        "host": _safe_str(principal.get("hostname") or event.get("source", {}).get("host")),
        "protocol": _safe_str(artifacts.get("protocol")).lower(),
        "action": _safe_str(artifacts.get("action")).lower(),
    }
    return {name: value for name, value in keys.items() if value}


def build_behavioral_numeric_features(event: dict[str, Any]) -> dict[str, float]:
    principal = event.get("principal", {})
    artifacts = event.get("artifacts", {})
    parsed_time = _parse_event_time(_safe_str(event.get("event_time")))

    src_ip = _safe_str(principal.get("src_ip"))
    dest_ip = _safe_str(principal.get("dest_ip"))
    request_path = _safe_str(artifacts.get("request_path")).lower()
    protocol = _safe_str(artifacts.get("protocol")).lower()
    action = _safe_str(artifacts.get("action")).lower()
    bytes_transferred = _safe_float(artifacts.get("bytes_transferred"))

    hour = float(parsed_time.hour) if parsed_time else 0.0
    weekday = float(parsed_time.weekday()) if parsed_time else 0.0

    return {
        "hour_of_day": hour,
        "day_of_week": weekday,
        "is_weekend": float(weekday >= 5),
        "bytes_log": log1p(max(bytes_transferred, 0.0)),
        "source_is_internal": float(_is_internal(src_ip)),
        "dest_is_internal": float(_is_internal(dest_ip)),
        "cross_boundary": float(bool(src_ip and dest_ip) and _is_internal(src_ip) != _is_internal(dest_ip)),
        "is_login_path": float("/login" in request_path),
        "is_admin_path": float("/admin" in request_path or "/auth" in request_path or "/config" in request_path),
        "is_sensitive_protocol": float(protocol in {"ssh", "ftp", "rdp"}),
        "is_blocked": float(action == "blocked"),
        "is_alert_event": float(_safe_str(event.get("event_kind")).lower() == "alert"),
    }


def build_behavioral_hash_features(event: dict[str, Any]) -> dict[str, float | str]:
    artifacts = event.get("artifacts", {})
    numeric = build_behavioral_numeric_features(event)
    output: dict[str, float | str] = dict(numeric)
    output.update(
        {
            "event_kind": _safe_str(event.get("event_kind")).lower() or "unknown",
            "severity": _safe_str(event.get("severity")).lower() or "unknown",
            "protocol": _safe_str(artifacts.get("protocol")).lower() or "unknown",
            "action": _safe_str(artifacts.get("action")).lower() or "unknown",
            "request_path_prefix": _safe_str(artifacts.get("request_path")).lower()[:24],
            "user_agent_family": _user_agent_family(_safe_str(artifacts.get("user_agent"))),
        }
    )
    for name, value in build_entity_keys(event).items():
        output[f"entity_{name}"] = value
    return output


def group_events_by_entity(events: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for event in events:
        for entity_type, entity_value in build_entity_keys(event).items():
            grouped[entity_type][entity_value].append(event)
    return grouped
