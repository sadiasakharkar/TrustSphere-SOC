from pathlib import Path

from correlation.incident_builder import build_incidents
from feedback_loop.analyst_feedback.feedback_models import AnalystFeedbackRecord
from feedback_loop.analyst_feedback.feedback_store import append_feedback, load_feedback
from feedback_loop.retraining_signals.retraining_dataset import export_retraining_examples
from ingestion.adapters.normalize_records import ingest_and_normalize
from prioritization.ranking.prioritize_incidents import prioritize_incidents


def _ranked_incidents() -> list[dict]:
    events = list(
        ingest_and_normalize(
            Path("tests/fixtures/correlation_events.json"),
            dataset_id="cyber_threat_logs_v1",
            domain="network_security",
        )
    )
    return prioritize_incidents(build_incidents(events), feedback_path=None)


def test_feedback_store_roundtrip(tmp_path: Path) -> None:
    feedback_path = tmp_path / "feedback.jsonl"
    append_feedback(
        AnalystFeedbackRecord(
            incident_id="INC-00001",
            analyst_id="analyst-1",
            verdict="true_positive",
            playbook_usefulness="useful",
        ),
        path=feedback_path,
    )
    records = load_feedback(feedback_path)
    assert len(records) == 1
    assert records[0]["verdict"] == "true_positive"


def test_retraining_export_uses_feedback(tmp_path: Path) -> None:
    ranked = _ranked_incidents()
    feedback_path = tmp_path / "feedback.jsonl"
    append_feedback(
        AnalystFeedbackRecord(
            incident_id=ranked[0]["incident_id"],
            analyst_id="analyst-1",
            verdict="true_positive",
            playbook_usefulness="useful",
        ),
        path=feedback_path,
    )
    output_path = tmp_path / "retraining.jsonl"
    exported = export_retraining_examples(ranked, load_feedback(feedback_path), path=output_path)
    assert exported == 1
    assert output_path.exists()
