from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class EntityBehaviorScore:
    final_score: float
    label: str
    global_score: float
    entity_score: float
    entity_breakdown: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_entity_behavior(model_result: dict[str, Any]) -> EntityBehaviorScore:
    final_score = float(model_result["final_score"])
    return EntityBehaviorScore(
        final_score=round(final_score, 4),
        label=str(model_result["label"]),
        global_score=round(float(model_result["global_score"]), 4),
        entity_score=round(float(model_result["entity_score"]), 4),
        entity_breakdown=model_result["entity_breakdown"],
    )
