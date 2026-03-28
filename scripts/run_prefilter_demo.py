from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.adapters.normalize_records import ingest_and_normalize
from prefiltering.pipeline import PrefilteringPipeline


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/run_prefilter_demo.py <artifact_dir> <input_path> <dataset_id> [domain] [limit]")
        raise SystemExit(1)

    artifact_dir = Path(sys.argv[1])
    input_path = Path(sys.argv[2])
    dataset_id = sys.argv[3]
    domain = sys.argv[4] if len(sys.argv) > 4 else "network_security"
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 5

    pipeline = PrefilteringPipeline.load_from_artifacts(artifact_dir)
    for index, canonical_event in enumerate(
        ingest_and_normalize(input_path, dataset_id=dataset_id, domain=domain),
        start=1,
    ):
        raw_row = {
            "source_ip": canonical_event["principal"]["src_ip"],
            "dest_ip": canonical_event["principal"]["dest_ip"],
            "protocol": canonical_event["artifacts"]["protocol"],
            "action": canonical_event["artifacts"]["action"],
            "bytes_transferred": canonical_event["artifacts"]["bytes_transferred"],
            "user_agent": canonical_event["artifacts"]["user_agent"],
            "request_path": canonical_event["artifacts"]["request_path"],
            "log_type": canonical_event["event_kind"],
            "threat_label": canonical_event["labels"]["ground_truth"],
        }
        decision = pipeline.evaluate(dataset_id, canonical_event, raw_row)
        print(json.dumps({"event_id": canonical_event["event_id"], "decision": decision.to_dict()}, indent=2))
        if index >= limit:
            break


if __name__ == "__main__":
    main()
