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


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/run_prioritization_demo.py <input_path> <dataset_id> <domain> [limit]")
        raise SystemExit(1)

    input_path = Path(sys.argv[1])
    dataset_id = sys.argv[2]
    domain = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    events = []
    for index, event in enumerate(ingest_and_normalize(input_path, dataset_id=dataset_id, domain=domain), start=1):
        events.append(event)
        if index >= limit:
            break

    incidents = build_incidents(events)
    ranked = prioritize_incidents(incidents)
    payload = {
        "incident_count": len(incidents),
        "ranked_count": len(ranked),
        "llm_candidate_count": len(llm_candidate_incidents(ranked)),
        "top_ranked": ranked[:3],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
