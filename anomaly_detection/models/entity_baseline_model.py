from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import sys
from typing import Any

VENDOR_DIR = Path(__file__).resolve().parents[2] / ".vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import joblib

from anomaly_detection.feature_engineering.behavioral_features import (
    build_behavioral_numeric_features,
    build_entity_keys,
)


@dataclass(slots=True)
class RunningStats:
    count: int = 0
    total: float = 0.0
    total_sq: float = 0.0
    hour_histogram: Counter[int] = field(default_factory=Counter)
    action_counts: Counter[str] = field(default_factory=Counter)
    protocol_counts: Counter[str] = field(default_factory=Counter)

    def update(self, *, hour: int, bytes_log: float, action: str, protocol: str) -> None:
        self.count += 1
        self.total += bytes_log
        self.total_sq += bytes_log * bytes_log
        self.hour_histogram[hour] += 1
        self.action_counts[action] += 1
        self.protocol_counts[protocol] += 1

    @property
    def mean(self) -> float:
        return self.total / self.count if self.count else 0.0

    @property
    def std(self) -> float:
        if self.count <= 1:
            return 0.0
        variance = max((self.total_sq / self.count) - (self.mean * self.mean), 0.0)
        return sqrt(variance)


class EntityBaselineModel:
    def __init__(self) -> None:
        self.entity_profiles: dict[str, dict[str, RunningStats]] = defaultdict(dict)
        self.global_stats = RunningStats()
        self._fitted = False

    def fit(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            numeric = build_behavioral_numeric_features(event)
            hour = int(numeric["hour_of_day"])
            bytes_log = float(numeric["bytes_log"])
            artifacts = event.get("artifacts", {})
            action = str(artifacts.get("action") or "unknown").lower()
            protocol = str(artifacts.get("protocol") or "unknown").lower()

            self.global_stats.update(hour=hour, bytes_log=bytes_log, action=action, protocol=protocol)
            for entity_type, entity_value in build_entity_keys(event).items():
                if entity_value not in self.entity_profiles[entity_type]:
                    self.entity_profiles[entity_type][entity_value] = RunningStats()
                self.entity_profiles[entity_type][entity_value].update(
                    hour=hour,
                    bytes_log=bytes_log,
                    action=action,
                    protocol=protocol,
                )
        self._fitted = True

    def _score_profile(self, stats: RunningStats, *, hour: int, bytes_log: float, action: str, protocol: str) -> float:
        score = 0.0
        if stats.count <= 1:
            return 0.55

        std = stats.std
        if std > 0:
            z_score = abs(bytes_log - stats.mean) / std
            score += min(z_score / 4.0, 1.0) * 0.35

        hour_probability = stats.hour_histogram[hour] / stats.count if stats.count else 0.0
        score += (1.0 - min(hour_probability * 4.0, 1.0)) * 0.25

        action_probability = stats.action_counts[action] / stats.count if stats.count else 0.0
        protocol_probability = stats.protocol_counts[protocol] / stats.count if stats.count else 0.0
        score += (1.0 - min(action_probability * 3.0, 1.0)) * 0.20
        score += (1.0 - min(protocol_probability * 3.0, 1.0)) * 0.20
        return max(0.0, min(score, 1.0))

    def score_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self._fitted:
            raise ValueError("EntityBaselineModel must be fitted before scoring")

        numeric = build_behavioral_numeric_features(event)
        hour = int(numeric["hour_of_day"])
        bytes_log = float(numeric["bytes_log"])
        artifacts = event.get("artifacts", {})
        action = str(artifacts.get("action") or "unknown").lower()
        protocol = str(artifacts.get("protocol") or "unknown").lower()

        entity_scores: dict[str, dict[str, Any]] = {}
        component_scores: list[float] = []
        for entity_type, entity_value in build_entity_keys(event).items():
            stats = self.entity_profiles.get(entity_type, {}).get(entity_value)
            if stats is None:
                entity_score = 0.75
                support = 0
            else:
                entity_score = self._score_profile(
                    stats,
                    hour=hour,
                    bytes_log=bytes_log,
                    action=action,
                    protocol=protocol,
                )
                support = stats.count
            entity_scores[entity_type] = {
                "entity": entity_value,
                "score": round(entity_score, 4),
                "support": support,
            }
            component_scores.append(entity_score)

        global_score = self._score_profile(
            self.global_stats,
            hour=hour,
            bytes_log=bytes_log,
            action=action,
            protocol=protocol,
        )
        component_scores.append(global_score)

        aggregate = sum(component_scores) / len(component_scores) if component_scores else global_score
        return {
            "entity_scores": entity_scores,
            "global_score": round(global_score, 4),
            "aggregate_score": round(aggregate, 4),
            "label": "anomalous" if aggregate >= 0.6 else "normal",
        }

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "entity_profiles": self.entity_profiles,
                "global_stats": self.global_stats,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> "EntityBaselineModel":
        payload = joblib.load(path)
        instance = cls()
        instance.entity_profiles = payload["entity_profiles"]
        instance.global_stats = payload["global_stats"]
        instance._fitted = True
        return instance
