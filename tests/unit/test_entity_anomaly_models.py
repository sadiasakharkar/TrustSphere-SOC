from pathlib import Path

from anomaly_detection.feature_engineering.behavioral_features import (
    build_behavioral_hash_features,
    build_entity_keys,
)
from anomaly_detection.models.entity_anomaly_ensemble import EntityAnomalyEnsemble
from ingestion.adapters.normalize_records import ingest_and_normalize


def _sample_events() -> list[dict]:
    return list(
        ingest_and_normalize(
            Path("tests/fixtures/sample_events.csv"),
            dataset_id="cyber_threat_logs_v1",
            domain="network_security",
        )
    )


def test_behavioral_features_include_entity_dimensions() -> None:
    event = _sample_events()[0]
    keys = build_entity_keys(event)
    features = build_behavioral_hash_features(event)
    assert "src_ip" in keys
    assert "entity_src_ip" in features
    assert "hour_of_day" in features


def test_entity_anomaly_ensemble_scores_events() -> None:
    events = _sample_events()
    model = EntityAnomalyEnsemble()
    model.fit(events)
    result = model.score_event(events[0])
    assert result["label"] in {"normal", "anomalous"}
    assert "src_ip" in result["entity_breakdown"]
