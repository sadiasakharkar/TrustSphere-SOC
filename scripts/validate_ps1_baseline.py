from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from correlation.incident_builder import build_incidents
from ingestion.adapters.normalize_records import ingest_and_normalize
from prioritization.ranking.prioritize_incidents import llm_candidate_incidents, prioritize_incidents


def _process_file(path: Path, dataset_id: str, domain: str) -> dict:
    events = list(ingest_and_normalize(path, dataset_id=dataset_id, domain=domain))
    incidents = build_incidents(events)
    ranked = prioritize_incidents(incidents)
    return {
        "file": str(path),
        "normalized_events": len(events),
        "incidents": len(incidents),
        "llm_candidates": len(llm_candidate_incidents(ranked)),
        "top_priority_score": ranked[0]["priority_score"] if ranked else 0.0,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_ps1_baseline.py <ps1_dir>")
        raise SystemExit(1)

    ps1_dir = Path(sys.argv[1])
    files = [
        ps1_dir / "ps1_disrupted.csv",
        ps1_dir / "ps1_disrupted.json",
        ps1_dir / "ps1_disrupted.syslog",
    ]
    results = []
    for path in files:
        if not path.exists():
            continue
        results.append(_process_file(path, "cyber_threat_logs_v1", "network_security"))

    baseline = {
        "ps1_dir": str(ps1_dir),
        "checked_files": len(results),
        "results": results,
        "baseline_stable": all(item["normalized_events"] > 0 and item["incidents"] > 0 for item in results),
    }
    output_path = ROOT / "artifacts" / "ps1_validation_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    main()
