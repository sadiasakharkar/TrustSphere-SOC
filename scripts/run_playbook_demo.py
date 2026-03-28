from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from correlation.incident_builder import build_incidents
from ingestion.adapters.normalize_records import ingest_and_normalize
from playbook_generation.recommendations.playbook_generator import generate_candidate_playbooks
from prioritization.ranking.prioritize_incidents import prioritize_incidents


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/run_playbook_demo.py <input_path> <dataset_id> <domain> [limit] [provider]")
        raise SystemExit(1)

    input_path = Path(sys.argv[1])
    dataset_id = sys.argv[2]
    domain = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 50
    provider = sys.argv[5] if len(sys.argv) > 5 else None

    events = []
    for index, event in enumerate(ingest_and_normalize(input_path, dataset_id=dataset_id, domain=domain), start=1):
        events.append(event)
        if index >= limit:
            break

    incidents = build_incidents(events)
    ranked = prioritize_incidents(incidents)
    playbooks = generate_candidate_playbooks(ranked, provider=provider)
    print(json.dumps({"candidate_count": len(playbooks), "playbooks": playbooks}, indent=2))


if __name__ == "__main__":
    main()
