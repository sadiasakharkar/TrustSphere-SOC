from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.adapters.normalize_records import ingest_and_normalize


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/run_normalization_demo.py <path> <dataset_id> <domain> [limit]")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    dataset_id = sys.argv[2]
    domain = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    for index, event in enumerate(
        ingest_and_normalize(path, dataset_id=dataset_id, domain=domain),
        start=1,
    ):
        print(json.dumps(event, indent=2))
        if index >= limit:
            break


if __name__ == "__main__":
    main()
