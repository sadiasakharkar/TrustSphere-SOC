from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from feedback_loop.analyst_feedback.feedback_store import load_feedback
from feedback_loop.retraining_signals.signal_builder import build_feedback_signal_map, incident_feedback_signature
from prioritization.models.priority_record import PriorityRecord
from prioritization.risk_engine.asset_context import asset_score_for_incident, load_asset_context


SEVERITY_ORDER = {"unknown": 0.1, "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
SUSPICIOUS_ACTION_KEYWORDS = (
    "new-inboxrule",
    "mailitemsaccessed",
    "filedownloaded",
    "send",
    "process_create",
    "cmd.exe",
    "powershell",
    "login_fail",
    "rdp_login",
    "access_denied",
    "alert",
    "file_write",
)
SUSPICIOUS_PATH_KEYWORDS = (
    "xp_cmdshell",
    "sp_configure",
    "union select",
    "../",
    "/admin",
    "/login",
    "wire_transfer",
)
SUSPICIOUS_BODY_KEYWORDS = (
    "cmd.exe",
    "powershell",
    "whoami",
    "ipconfig",
    "forwardto",
    "deletemessage",
)


def _prefilter_score(incident: dict[str, Any]) -> float:
    values = []
    for evidence in incident.get("evidence_bundle", []):
        labels = evidence.get("labels", {})
        prefilter_label = labels.get("prefilter_label")
        if prefilter_label == "true_positive":
            values.append(0.95)
        elif prefilter_label == "uncertain":
            values.append(0.55)
        elif prefilter_label == "false_positive":
            values.append(0.15)
    if values:
        return sum(values) / len(values)
    return float(incident.get("confidence", 0.5))


def _anomaly_score(incident: dict[str, Any]) -> float:
    scores = []
    for evidence in incident.get("evidence_bundle", []):
        anomaly = evidence.get("anomaly") or {}
        for key in ("final_score", "normalized_score", "aggregate_score"):
            if key in anomaly:
                scores.append(float(anomaly[key]))
                break
    if scores:
        return sum(scores) / len(scores)
    return float(incident.get("summary", {}).get("average_anomaly_score", 0.0))


def _severity_score(incident: dict[str, Any], asset_context: dict[str, Any]) -> float:
    severity = str(incident.get("severity", "unknown"))
    return float(asset_context.get("severity_weights", {}).get(severity, SEVERITY_ORDER.get(severity, 0.1)))


def _recurrence_scores(incidents: list[dict[str, Any]]) -> dict[str, float]:
    key_counts = Counter()
    incident_keys: dict[str, str] = {}
    for incident in incidents:
        entities = incident.get("entities", {})
        key = "|".join(
            [
                ",".join(entities.get("src_ips", [])),
                ",".join(entities.get("dest_ips", [])),
                ",".join(entities.get("actions", [])),
                ",".join(entities.get("protocols", [])),
            ]
        )
        incident_keys[incident["incident_id"]] = key
        key_counts[key] += 1

    return {
        incident_id: min(1.0, 0.25 + ((key_counts[key] - 1) * 0.25))
        for incident_id, key in incident_keys.items()
    }


def _priority_label(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _heuristic_threat_score(incident: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    summary = incident.get("summary", {})
    event_kinds = set(summary.get("event_kinds", []))
    evidence_bundle = incident.get("evidence_bundle", [])

    if len(event_kinds) >= 2:
        score += 0.14
        reasons.append("multi-stage incident chain")
    if int(summary.get("event_count", 0)) >= 3:
        score += 0.10
        reasons.append("multiple related events")

    for evidence in evidence_bundle:
        artifacts = evidence.get("artifacts", {})
        feature_map = artifacts.get("feature_map", {})
        action_text = str(artifacts.get("action") or "").lower()
        path_text = str(artifacts.get("request_path") or "").lower()
        body_text = str(artifacts.get("body") or "").lower()
        feature_blob = str(feature_map).lower()

        if any(keyword in action_text for keyword in SUSPICIOUS_ACTION_KEYWORDS):
            score += 0.09
            if "suspicious execution or mailbox action" not in reasons:
                reasons.append("suspicious execution or mailbox action")
        if any(keyword in path_text for keyword in SUSPICIOUS_PATH_KEYWORDS):
            score += 0.15
            if "exploit-like request pattern" not in reasons:
                reasons.append("exploit-like request pattern")
        if any(keyword in body_text for keyword in SUSPICIOUS_BODY_KEYWORDS):
            score += 0.14
            if "high-risk command content" not in reasons:
                reasons.append("high-risk command content")
        if "suspiciousipaddress" in feature_blob or "unfamiliarfeatures" in feature_blob:
            score += 0.15
            if "risky sign-in indicators" not in reasons:
                reasons.append("risky sign-in indicators")
        if "forwardto" in feature_blob or "deletemessage" in feature_blob:
            score += 0.12
            if "mail forwarding or deletion rule" not in reasons:
                reasons.append("mail forwarding or deletion rule")
        if "sqlservr.exe" in feature_blob and "cmd.exe" in body_text:
            score += 0.18
            if "service-spawned shell execution" not in reasons:
                reasons.append("service-spawned shell execution")

    return min(score, 0.45), reasons


def _incident_strength_bonus(incident: dict[str, Any], prefilter: float, asset_score: float, severity: float) -> float:
    summary = incident.get("summary", {})
    event_count = int(summary.get("event_count", 0))
    duplicate_total = int(summary.get("duplicate_total", 0))
    bonus = 0.0
    if event_count >= 2:
        bonus += 0.03
    if duplicate_total >= 2:
        bonus += 0.02
    if severity >= 1.0 and asset_score >= 1.0 and prefilter >= 0.9:
        bonus += 0.05
    return min(bonus, 0.08)


def _llm_escalation_override(
    *,
    priority_score: float,
    confidence: float,
    severity: float,
    prefilter: float,
    threat_heuristic: float,
    minimum_priority: float,
    minimum_confidence: float,
) -> bool:
    if priority_score >= minimum_priority and confidence >= minimum_confidence:
        return True
    if confidence < minimum_confidence:
        return False
    if severity >= 1.0 and prefilter >= 0.9:
        return True
    if severity >= 0.75 and threat_heuristic >= 0.35 and priority_score >= max(0.45, minimum_priority - 0.15):
        return True
    return False


def prioritize_incidents(
    incidents: list[dict[str, Any]],
    *,
    asset_context_path: str | Path = Path("configs/asset_context.json"),
    feedback_path: str | Path | None = Path("feedback_loop/analyst_feedback/feedback_log.jsonl"),
) -> list[dict[str, Any]]:
    asset_context = load_asset_context(asset_context_path)
    recurrence_scores = _recurrence_scores(incidents)
    raw_priority_records: list[dict[str, Any]] = []
    llm_thresholds = asset_context.get("llm_thresholds", {})
    minimum_priority = float(llm_thresholds.get("minimum_priority_score", 0.68))
    minimum_confidence = float(llm_thresholds.get("minimum_confidence", 0.72))

    for incident in incidents:
        prefilter = _prefilter_score(incident)
        anomaly = _anomaly_score(incident)
        severity = _severity_score(incident, asset_context)
        recurrence = recurrence_scores.get(incident["incident_id"], 0.25)
        asset_score, asset_reasons = asset_score_for_incident(incident, asset_context)
        confidence = float(incident.get("confidence", 0.0))
        strength_bonus = _incident_strength_bonus(incident, prefilter, asset_score, severity)
        threat_heuristic, threat_reasons = _heuristic_threat_score(incident)

        priority_score = (
            prefilter * 0.24
            + anomaly * 0.18
            + severity * 0.18
            + recurrence * 0.10
            + asset_score * 0.15
            + threat_heuristic * 0.15
            + strength_bonus
        )
        llm_eligible = _llm_escalation_override(
            priority_score=priority_score,
            confidence=confidence,
            severity=severity,
            prefilter=prefilter,
            threat_heuristic=threat_heuristic,
            minimum_priority=minimum_priority,
            minimum_confidence=minimum_confidence,
        )
        reasons = list(asset_reasons) + threat_reasons
        if recurrence > 0.4:
            reasons.append("recurring incident pattern")
        if anomaly >= 0.6:
            reasons.append("strong anomaly score")
        if prefilter >= 0.7:
            reasons.append("high prefilter confidence")

        record = PriorityRecord(
            incident_id=incident["incident_id"],
            priority_score=round(priority_score, 4),
            priority_label=_priority_label(priority_score),
            llm_eligible=llm_eligible,
            score_breakdown={
                "prefilter": round(prefilter, 4),
                "anomaly": round(anomaly, 4),
                "severity": round(severity, 4),
                "recurrence": round(recurrence, 4),
                "asset_context": round(asset_score, 4),
                "threat_heuristic": round(threat_heuristic, 4),
                "strength_bonus": round(strength_bonus, 4),
                "confidence": round(confidence, 4),
            },
            reasons=reasons,
            incident=incident,
        )
        raw_priority_records.append(record.to_dict())

    if feedback_path is not None:
        feedback_records = load_feedback(feedback_path)
        signal_map = build_feedback_signal_map(raw_priority_records, feedback_records)
        signature_signal_map = {
            signal["signature"]: signal["boost_score"]
            for signal in signal_map.values()
        }
        for record in raw_priority_records:
            signature = incident_feedback_signature(record["incident"])
            boost = signature_signal_map.get(signature, 0.0)
            if boost:
                record["priority_score"] = round(max(0.0, min(record["priority_score"] + boost, 1.0)), 4)
                record["priority_label"] = _priority_label(record["priority_score"])
                record["score_breakdown"]["feedback_boost"] = round(boost, 4)
                record["reasons"].append("analyst feedback adjustment")
                record["llm_eligible"] = (
                    _llm_escalation_override(
                        priority_score=float(record["priority_score"]),
                        confidence=float(record["incident"].get("confidence", 0.0)),
                        severity=float(record["score_breakdown"].get("severity", 0.0)),
                        prefilter=float(record["score_breakdown"].get("prefilter", 0.0)),
                        threat_heuristic=float(record["score_breakdown"].get("threat_heuristic", 0.0)),
                        minimum_priority=minimum_priority,
                        minimum_confidence=minimum_confidence,
                    )
                )

    raw_priority_records.sort(
        key=lambda item: (item["priority_score"], item["incident"]["confidence"], item["incident"]["start_time"]),
        reverse=True,
    )
    return raw_priority_records


def llm_candidate_incidents(priority_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in priority_records if record["llm_eligible"]]
