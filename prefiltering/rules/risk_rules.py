from __future__ import annotations

from dataclasses import dataclass, asdict
from ipaddress import ip_address, ip_network
from math import log1p
from typing import Any


INTERNAL_NETWORKS = (
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
)

HIGH_RISK_PATH_MARKERS = ("/admin", "/auth", "/config", "/login", "/wp-admin")
SCANNER_MARKERS = ("nmap", "sqlmap", "nikto", "masscan")
SUSPICIOUS_UA_MARKERS = ("curl", "python-requests", "wget")


@dataclass(slots=True)
class RuleEvaluation:
    score: float
    label: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_internal(ip_value: str | None) -> bool:
    if not ip_value:
        return False
    try:
        candidate = ip_address(ip_value)
    except ValueError:
        return False
    return any(candidate in network for network in INTERNAL_NETWORKS)


def _normalized_lower(value: Any) -> str:
    return str(value or "").strip().lower()


def evaluate_risk_rules(event: dict[str, Any]) -> RuleEvaluation:
    score = 0.0
    reasons: list[str] = []

    severity = _normalized_lower(event.get("severity"))
    event_kind = _normalized_lower(event.get("event_kind"))
    principal = event.get("principal", {})
    artifacts = event.get("artifacts", {})
    labels = event.get("labels", {})

    protocol = _normalized_lower(artifacts.get("protocol"))
    action = _normalized_lower(artifacts.get("action"))
    user_agent = _normalized_lower(artifacts.get("user_agent"))
    request_path = _normalized_lower(artifacts.get("request_path"))
    bytes_transferred = artifacts.get("bytes_transferred") or 0
    try:
        bytes_numeric = int(bytes_transferred)
    except (TypeError, ValueError):
        bytes_numeric = 0

    if severity == "critical":
        score += 40
        reasons.append("critical severity")
    elif severity == "high":
        score += 25
        reasons.append("high severity")
    elif severity == "medium":
        score += 15
        reasons.append("medium severity")

    if event_kind in {"alert", "network"}:
        score += 8
        reasons.append(f"{event_kind} event")

    if protocol in {"ssh", "ftp"}:
        score += 10
        reasons.append(f"sensitive protocol {protocol}")
    elif protocol in {"http", "https"} and any(marker in request_path for marker in HIGH_RISK_PATH_MARKERS):
        score += 12
        reasons.append("high risk request path")

    if action == "blocked":
        score += 8
        reasons.append("blocked action")
    elif action == "allowed":
        score -= 5
        reasons.append("allowed action")

    if any(marker in user_agent for marker in SCANNER_MARKERS):
        score += 20
        reasons.append("scanner-like user agent")
    elif any(marker in user_agent for marker in SUSPICIOUS_UA_MARKERS):
        score += 10
        reasons.append("suspicious automation user agent")

    if bytes_numeric:
        score += min(10.0, log1p(bytes_numeric) / 2.0)
        if bytes_numeric > 25000:
            reasons.append("high data volume")

    src_ip = principal.get("src_ip")
    dest_ip = principal.get("dest_ip")
    if src_ip and dest_ip and (_is_internal(src_ip) != _is_internal(dest_ip)):
        score += 12
        reasons.append("cross-boundary traffic")

    ground_truth = _normalized_lower(labels.get("ground_truth"))
    if ground_truth == "malicious":
        score += 20
        reasons.append("ground truth malicious")
    elif ground_truth == "suspicious":
        score += 10
        reasons.append("ground truth suspicious")
    elif ground_truth in {"benign", "0"}:
        score -= 10
        reasons.append("ground truth benign")

    score = max(0.0, min(score, 100.0))
    if score >= 65:
        label = "true_positive"
    elif score <= 25:
        label = "false_positive"
    else:
        label = "uncertain"

    return RuleEvaluation(score=round(score, 3), label=label, reasons=reasons)
