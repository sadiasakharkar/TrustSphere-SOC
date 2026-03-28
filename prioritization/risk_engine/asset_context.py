from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_asset_context(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def asset_score_for_incident(incident: dict[str, Any], asset_context: dict[str, Any]) -> tuple[float, list[str]]:
    critical_assets = asset_context.get("critical_assets", {})
    asset_weights = asset_context.get("asset_weights", {})
    entities = incident.get("entities", {})
    evidence_bundle = incident.get("evidence_bundle", [])

    best_level = "unknown"
    reasons: list[str] = []

    ip_context = critical_assets.get("ips", {})
    for ip in entities.get("dest_ips", []) + entities.get("src_ips", []):
        level = ip_context.get(ip)
        if level and asset_weights.get(level, 0.0) >= asset_weights.get(best_level, 0.0):
            best_level = level
            reasons.append(f"asset ip {ip} tagged {level}")

    host_context = critical_assets.get("hosts", {})
    for host in entities.get("hosts", []):
        level = host_context.get(host)
        if level and asset_weights.get(level, 0.0) >= asset_weights.get(best_level, 0.0):
            best_level = level
            reasons.append(f"host {host} tagged {level}")

    path_context = critical_assets.get("paths", {})
    for evidence in evidence_bundle:
        path = str(evidence.get("artifacts", {}).get("request_path") or "")
        for known_path, level in path_context.items():
            if path.startswith(known_path) and asset_weights.get(level, 0.0) >= asset_weights.get(best_level, 0.0):
                best_level = level
                reasons.append(f"path {known_path} tagged {level}")

    return float(asset_weights.get(best_level, asset_weights.get("unknown", 0.15))), reasons
