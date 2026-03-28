from pathlib import Path

from ingestion.adapters.normalize_records import ingest_and_normalize


def test_csv_ingestion_normalizes_fields() -> None:
    path = Path("tests/fixtures/sample_events.csv")
    events = list(ingest_and_normalize(path, dataset_id="csv_demo", domain="network_security"))
    assert len(events) == 2
    assert events[0]["principal"]["src_ip"] == "192.168.1.125"
    assert events[1]["severity"] == "high"


def test_json_ingestion_maps_aliases() -> None:
    path = Path("tests/fixtures/sample_events.json")
    events = list(ingest_and_normalize(path, dataset_id="json_demo", domain="network_security"))
    assert len(events) == 2
    assert events[0]["principal"]["src_ip"] == "10.0.0.10"
    assert events[0]["severity"] == "critical"


def test_syslog_ingestion_handles_missing_timestamp_alias() -> None:
    path = Path("tests/fixtures/sample_events.syslog")
    events = list(ingest_and_normalize(path, dataset_id="syslog_demo", domain="network_security"))
    assert len(events) == 2
    assert events[0]["principal"]["src_ip"] == "192.168.1.55"
    assert events[1]["event_time"]
