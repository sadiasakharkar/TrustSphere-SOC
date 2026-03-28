from pathlib import Path

from correlation.incident_builder import build_incidents
from ingestion.adapters.normalize_records import ingest_and_normalize
from prioritization.ranking.prioritize_incidents import llm_candidate_incidents, prioritize_incidents


def _incidents() -> list[dict]:
    events = list(
        ingest_and_normalize(
            Path("tests/fixtures/correlation_events.json"),
            dataset_id="cyber_threat_logs_v1",
            domain="network_security",
        )
    )
    return build_incidents(events)


def test_prioritization_ranks_incidents() -> None:
    ranked = prioritize_incidents(_incidents())
    assert len(ranked) == 2
    assert ranked[0]["priority_score"] >= ranked[1]["priority_score"]
    assert ranked[0]["priority_label"] in {"critical", "high", "medium", "low"}


def test_llm_candidates_are_filtered_from_ranked_incidents() -> None:
    ranked = prioritize_incidents(_incidents())
    candidates = llm_candidate_incidents(ranked)
    assert len(candidates) <= len(ranked)
    assert all(item["llm_eligible"] for item in candidates)
