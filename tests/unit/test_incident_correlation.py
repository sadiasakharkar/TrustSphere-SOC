from pathlib import Path

from correlation.incident_builder import build_incidents
from correlation.timeline_reconstruction.timeline_builder import reconstruct_timeline
from ingestion.adapters.normalize_records import ingest_and_normalize


def _events() -> list[dict]:
    return list(
        ingest_and_normalize(
            Path("tests/fixtures/correlation_events.json"),
            dataset_id="cyber_threat_logs_v1",
            domain="network_security",
        )
    )


def test_timeline_reconstruction_orders_shuffled_events() -> None:
    timeline = reconstruct_timeline(_events()[:3])
    assert timeline[0]["event_time"] < timeline[-1]["event_time"]
    assert timeline[0]["sequence"] == 1


def test_incident_builder_merges_duplicates_and_groups_related_events() -> None:
    incidents = build_incidents(_events())
    assert len(incidents) == 2
    primary = incidents[0]
    assert primary["summary"]["duplicate_total"] >= 2
    assert len(primary["timeline"]) >= 2
    assert len(primary["evidence_bundle"]) >= 2
