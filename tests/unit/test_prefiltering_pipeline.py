from pathlib import Path

from ingestion.adapters.normalize_records import ingest_and_normalize
from prefiltering.fusion.decision_fusion import fuse_decisions
from prefiltering.rules.risk_rules import evaluate_risk_rules


def test_rule_engine_flags_scanner_like_event() -> None:
    event = list(ingest_and_normalize(Path("tests/fixtures/sample_events.csv"), dataset_id="cyber_threat_logs_v1", domain="network_security"))[0]
    result = evaluate_risk_rules(event)
    assert result.score > 0
    assert "scanner-like user agent" in result.reasons


def test_decision_fusion_outputs_valid_label() -> None:
    decision = fuse_decisions(
        rule_score=72.0,
        rule_label="true_positive",
        ml_probabilities={"true_positive": 0.82, "false_positive": 0.08, "uncertain": 0.10},
        anomaly_score=0.73,
        auxiliary_scores={"email": 0.4},
        reasons=["high severity"],
    )
    assert decision.final_label in {"true_positive", "false_positive", "uncertain"}
    assert decision.final_score > 0
