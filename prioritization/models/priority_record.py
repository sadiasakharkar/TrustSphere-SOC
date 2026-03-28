from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class PriorityRecord:
    incident_id: str
    priority_score: float
    priority_label: str
    llm_eligible: bool
    score_breakdown: dict[str, float]
    reasons: list[str]
    incident: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
