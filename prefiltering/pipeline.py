from __future__ import annotations

from pathlib import Path
from typing import Any

from anomaly_detection.models.behavioral_anomaly_model import BehavioralAnomalyDetector
from prefiltering.fusion.decision_fusion import PrefilterDecision, fuse_decisions
from prefiltering.ml.supervised_model import StreamingEventClassifier
from prefiltering.rules.risk_rules import evaluate_risk_rules


class PrefilteringPipeline:
    def __init__(
        self,
        primary_classifier: StreamingEventClassifier,
        anomaly_detector: BehavioralAnomalyDetector,
        auxiliary_classifiers: dict[str, StreamingEventClassifier] | None = None,
    ) -> None:
        self.primary_classifier = primary_classifier
        self.anomaly_detector = anomaly_detector
        self.auxiliary_classifiers = auxiliary_classifiers or {}

    def evaluate(self, dataset_id: str, canonical_event: dict[str, Any], raw_row: dict[str, Any]) -> PrefilterDecision:
        rule_eval = evaluate_risk_rules(canonical_event)
        ml_prediction = self.primary_classifier.predict(dataset_id, raw_row)
        anomaly_prediction = self.anomaly_detector.score(dataset_id, raw_row)

        auxiliary_scores: dict[str, float] = {}
        if dataset_id in {"cyber_threat_logs_v1"}:
            if canonical_event.get("event_kind") == "email" and "email" in self.auxiliary_classifiers:
                auxiliary_scores["email"] = self.auxiliary_classifiers["email"].predict("email_text_v1", raw_row).probabilities.get("true_positive", 0.0)
            if canonical_event.get("event_kind") in {"url", "application", "network"} and "phishing" in self.auxiliary_classifiers:
                auxiliary_scores["phishing"] = self.auxiliary_classifiers["phishing"].predict("website_phishing_v1", raw_row).probabilities.get("true_positive", 0.0)

        return fuse_decisions(
            rule_score=rule_eval.score,
            rule_label=rule_eval.label,
            ml_probabilities=ml_prediction.probabilities,
            anomaly_score=float(anomaly_prediction["normalized_score"]),
            auxiliary_scores=auxiliary_scores,
            reasons=rule_eval.reasons,
        )

    @classmethod
    def load_from_artifacts(cls, artifact_dir: str | Path) -> "PrefilteringPipeline":
        artifact_dir = Path(artifact_dir)
        primary = StreamingEventClassifier.load(artifact_dir / "prefilter_primary.joblib")
        anomaly = BehavioralAnomalyDetector.load(artifact_dir / "prefilter_anomaly.joblib")
        auxiliary: dict[str, StreamingEventClassifier] = {}
        email_model = artifact_dir / "prefilter_email_aux.joblib"
        phishing_model = artifact_dir / "prefilter_phishing_aux.joblib"
        if email_model.exists():
            auxiliary["email"] = StreamingEventClassifier.load(email_model)
        if phishing_model.exists():
            auxiliary["phishing"] = StreamingEventClassifier.load(phishing_model)
        return cls(primary, anomaly, auxiliary)
