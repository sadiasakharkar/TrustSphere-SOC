from pathlib import Path

from correlation.incident_builder import build_incidents
from ingestion.adapters.normalize_records import ingest_and_normalize
from playbook_generation.serializers.evidence_serializer import serialize_incident_for_llm
from playbook_generation.recommendations.playbook_generator import generate_playbook_for_incident
from prioritization.ranking.prioritize_incidents import prioritize_incidents


def _priority_record() -> dict:
    events = list(
        ingest_and_normalize(
            Path("tests/fixtures/correlation_events.json"),
            dataset_id="cyber_threat_logs_v1",
            domain="network_security",
        )
    )
    ranked = prioritize_incidents(build_incidents(events))
    return ranked[0]


def test_evidence_serializer_uses_structured_fields() -> None:
    payload = serialize_incident_for_llm(_priority_record())
    assert "structured_evidence" in payload
    assert "incident_id" in payload
    assert "raw_ref" not in payload["structured_evidence"][0]


def test_playbook_generation_returns_approval_required_payload() -> None:
    result = generate_playbook_for_incident(_priority_record(), provider="ollama")
    assert result["analyst_only"] is True
    assert result["approval_required"] is True
    assert "playbook" in result
