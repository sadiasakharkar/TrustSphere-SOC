from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class AnalystFeedbackRecord:
    incident_id: str
    analyst_id: str
    verdict: str
    playbook_usefulness: str
    notes: str = ""
    created_at: str = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
