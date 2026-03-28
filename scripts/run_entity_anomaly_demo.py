from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anomaly_detection.models.entity_anomaly_ensemble import EntityAnomalyEnsemble
from anomaly_detection.scoring.entity_behavior_scorer import score_entity_behavior
from ingestion.adapters.normalize_records import ingest_and_normalize


def main() -> None:
    if len(sys.argv) < 5:
        print("Usage: python scripts/run_entity_anomaly_demo.py <artifact_path> <input_path> <dataset_id> <domain> [limit]")
        raise SystemExit(1)

    artifact_path = Path(sys.argv[1])
    input_path = Path(sys.argv[2])
    dataset_id = sys.argv[3]
    domain = sys.argv[4]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 5

    model = EntityAnomalyEnsemble.load(artifact_path)
    for index, event in enumerate(
        ingest_and_normalize(input_path, dataset_id=dataset_id, domain=domain),
        start=1,
    ):
        score = score_entity_behavior(model.score_event(event))
        print(json.dumps({"event_id": event["event_id"], "anomaly": score.to_dict()}, indent=2))
        if index >= limit:
            break


if __name__ == "__main__":
    main()
