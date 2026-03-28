from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from feedback_loop.analyst_feedback.feedback_store import load_feedback
from feedback_loop.retraining_signals.signal_builder import build_feedback_signal_map, incident_feedback_signature
from prioritization.models.priority_record import PriorityRecord
from prioritization.risk_engine.asset_context import asset_score_for_incident, load_asset_context


SEVERITY_ORDER = {"unknown": 0.1, "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}


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

        priority_score = (
            prefilter * 0.30
            + anomaly * 0.25
            + severity * 0.20
            + recurrence * 0.10
            + asset_score * 0.15
            + strength_bonus
        )
        llm_eligible = priority_score >= minimum_priority and confidence >= minimum_confidence
        reasons = list(asset_reasons)
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
                    record["priority_score"] >= minimum_priority
                    and float(record["incident"].get("confidence", 0.0)) >= minimum_confidence
                )

    raw_priority_records.sort(
        key=lambda item: (item["priority_score"], item["incident"]["confidence"], item["incident"]["start_time"]),
        reverse=True,
    )
    return raw_priority_records


def llm_candidate_incidents(priority_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in priority_records if record["llm_eligible"]]
