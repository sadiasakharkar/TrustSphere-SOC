from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any


INTERNAL_NETWORKS = (
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
)


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _is_internal(ip_value: str) -> bool:
    try:
        candidate = ip_address(ip_value)
    except ValueError:
        return False
    return any(candidate in network for network in INTERNAL_NETWORKS)


def _user_agent_family(user_agent: str) -> str:
    text = user_agent.lower()
    if "nmap" in text:
        return "nmap"
    if "curl" in text:
        return "curl"
    if "python" in text:
        return "python"
    if "mozilla" in text:
        return "browser"
    return "other"


def build_network_features(row: dict[str, Any]) -> dict[str, float | str]:
    src_ip = _safe_str(row.get("source_ip") or row.get("src_ip"))
    dest_ip = _safe_str(row.get("dest_ip") or row.get("destination_ip"))
    protocol = _safe_str(row.get("protocol") or row.get("proto")).lower() or "unknown"
    action = _safe_str(row.get("action") or row.get("decision")).lower() or "unknown"
    log_type = _safe_str(row.get("log_type") or row.get("event_category")).lower() or "unknown"
    user_agent = _safe_str(row.get("user_agent") or row.get("ua"))
    request_path = _safe_str(row.get("request_path") or row.get("uri"))
    bytes_value = row.get("bytes_transferred") or row.get("bytes_out") or 0
    try:
        bytes_numeric = float(bytes_value)
    except (TypeError, ValueError):
        bytes_numeric = 0.0

    features: dict[str, float | str] = {
        "protocol": protocol,
        "action": action,
        "log_type": log_type,
        "user_agent_family": _user_agent_family(user_agent),
        "request_path_prefix": request_path[:16].lower(),
        "source_is_internal": float(_is_internal(src_ip)),
        "dest_is_internal": float(_is_internal(dest_ip)),
        "cross_boundary": float(src_ip != "" and dest_ip != "" and _is_internal(src_ip) != _is_internal(dest_ip)),
        "bytes_transferred": bytes_numeric,
        "has_login_path": float("/login" in request_path.lower()),
        "has_admin_path": float("/admin" in request_path.lower() or "/auth" in request_path.lower()),
    }
    return features


def build_email_features(row: dict[str, Any]) -> dict[str, float | str]:
    subject = _safe_str(row.get("subject"))
    body = _safe_str(row.get("body") or row.get("text"))
    urls = _safe_str(row.get("urls"))
    return {
        "subject_len": float(len(subject)),
        "body_len": float(len(body)),
        "url_count_hint": float(urls.count("http")),
        "contains_discount": float("discount" in body.lower()),
        "contains_password": float("password" in body.lower() or "pw:" in body.lower()),
        "text_signature": f"{subject[:20].lower()}|{body[:20].lower()}|{urls[:20].lower()}",
    }


def build_url_features(row: dict[str, Any]) -> dict[str, float | str]:
    features: dict[str, float | str] = {}
    for key, value in row.items():
        if key.lower() in {"result", "label"}:
            continue
        try:
            numeric = float(value)
            features[key.lower()] = numeric + 2.0 if numeric < 0 else numeric
        except (TypeError, ValueError):
            features[key.lower()] = _safe_str(value).lower()
    return features


def build_features_for_dataset(dataset_id: str, row: dict[str, Any]) -> dict[str, float | str]:
    if dataset_id == "cyber_threat_logs_v1":
        return build_network_features(row)
    if dataset_id in {"email_text_v1", "nazario_email_url_v1"}:
        return build_email_features(row)
    return build_url_features(row)
