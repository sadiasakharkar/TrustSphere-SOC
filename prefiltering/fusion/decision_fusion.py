from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class PrefilterDecision:
    final_label: str
    final_score: float
    reasons: list[str]
    rule_score: float
    ml_probabilities: dict[str, float]
    anomaly_score: float
    auxiliary_scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fuse_decisions(
    *,
    rule_score: float,
    rule_label: str,
    ml_probabilities: dict[str, float],
    anomaly_score: float,
    auxiliary_scores: dict[str, float] | None = None,
    reasons: list[str] | None = None,
) -> PrefilterDecision:
    auxiliary_scores = auxiliary_scores or {}
    reasons = reasons or []

    true_positive_prob = ml_probabilities.get("true_positive", 0.0)
    false_positive_prob = ml_probabilities.get("false_positive", 0.0)
    uncertain_prob = ml_probabilities.get("uncertain", 0.0)
    auxiliary_boost = sum(auxiliary_scores.values()) / max(len(auxiliary_scores), 1) if auxiliary_scores else 0.0

    final_score = (
        (rule_score / 100.0) * 0.35
        + true_positive_prob * 0.40
        + anomaly_score * 0.20
        + auxiliary_boost * 0.05
    )
    false_signal = false_positive_prob * 0.50

    if rule_label == "true_positive" and (rule_score >= 65 or anomaly_score >= 0.45):
        label = "true_positive"
    elif rule_label == "false_positive" and rule_score <= 10 and anomaly_score < 0.35 and true_positive_prob < 0.15:
        label = "false_positive"
    elif final_score >= 0.68 and false_signal <= 0.25:
        label = "true_positive"
    elif false_signal >= 0.45 and anomaly_score < 0.45 and rule_label != "true_positive":
        label = "false_positive"
    else:
        label = "uncertain"

    if uncertain_prob >= 0.70 and label == "true_positive" and rule_label != "true_positive":
        label = "uncertain"
        reasons.append("high model uncertainty")

    return PrefilterDecision(
        final_label=label,
        final_score=round(final_score, 4),
        reasons=reasons,
        rule_score=rule_score,
        ml_probabilities={key: round(value, 4) for key, value in ml_probabilities.items()},
        anomaly_score=round(anomaly_score, 4),
        auxiliary_scores={key: round(value, 4) for key, value in auxiliary_scores.items()},
    )
