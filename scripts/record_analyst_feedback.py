from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from feedback_loop.analyst_feedback.feedback_models import AnalystFeedbackRecord
from feedback_loop.analyst_feedback.feedback_store import append_feedback


def main() -> None:
    if len(sys.argv) < 5:
        print("Usage: python scripts/record_analyst_feedback.py <incident_id> <analyst_id> <verdict> <playbook_usefulness> [notes]")
        raise SystemExit(1)

    record = AnalystFeedbackRecord(
        incident_id=sys.argv[1],
        analyst_id=sys.argv[2],
        verdict=sys.argv[3],
        playbook_usefulness=sys.argv[4],
        notes=sys.argv[5] if len(sys.argv) > 5 else "",
    )
    append_feedback(record)
    print(json.dumps(record.to_dict(), indent=2))


if __name__ == "__main__":
    main()
