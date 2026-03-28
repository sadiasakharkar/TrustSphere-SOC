from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def incident_feedback_signature(incident: dict[str, Any]) -> str:
    entities = incident.get("entities", {})
    parts = [
        ",".join(entities.get("src_ips", [])),
        ",".join(entities.get("dest_ips", [])),
        ",".join(entities.get("actions", [])),
        ",".join(entities.get("protocols", [])),
        incident.get("incident_type", "unknown"),
    ]
    return "|".join(parts)


def build_feedback_signal_map(priority_records: list[dict[str, Any]], feedback_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    incident_lookup = {record["incident_id"]: record["incident"] for record in priority_records}
    grouped_feedback: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for feedback in feedback_records:
        grouped_feedback[feedback["incident_id"]].append(feedback)

    signals: dict[str, dict[str, Any]] = {}
    for incident_id, feedback_list in grouped_feedback.items():
        incident = incident_lookup.get(incident_id)
        if not incident:
            continue
        signature = incident_feedback_signature(incident)
        verdict_counts = Counter(item["verdict"] for item in feedback_list)
        usefulness_counts = Counter(item["playbook_usefulness"] for item in feedback_list)
        signals[incident_id] = {
            "signature": signature,
            "verdict_counts": dict(verdict_counts),
            "playbook_usefulness_counts": dict(usefulness_counts),
            "total_feedback": len(feedback_list),
            "boost_score": _boost_from_feedback(verdict_counts, usefulness_counts),
        }
    return signals


def _boost_from_feedback(verdict_counts: Counter[str], usefulness_counts: Counter[str]) -> float:
    positive = verdict_counts.get("true_positive", 0)
    negative = verdict_counts.get("false_positive", 0)
    useful = usefulness_counts.get("useful", 0)
    not_useful = usefulness_counts.get("not_useful", 0)
    total = max(1, positive + negative + useful + not_useful)
    score = ((positive - negative) * 0.4 + (useful - not_useful) * 0.2) / total
    return max(-0.3, min(score, 0.3))
