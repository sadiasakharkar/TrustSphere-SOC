from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

VENDOR_DIR = Path(__file__).resolve().parents[2] / ".vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction import FeatureHasher

from anomaly_detection.feature_engineering.behavioral_features import build_behavioral_hash_features
from anomaly_detection.models.entity_baseline_model import EntityBaselineModel


class EntityAnomalyEnsemble:
    def __init__(self, n_features: int = 2**17, contamination: float = 0.06, n_estimators: int = 200) -> None:
        self.hasher = FeatureHasher(n_features=n_features, input_type="dict", alternate_sign=False)
        self.global_model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
            n_jobs=1,
        )
        self.entity_baseline = EntityBaselineModel()
        self._fitted = False

    def fit(self, events: list[dict[str, Any]]) -> None:
        feature_dicts = [build_behavioral_hash_features(event) for event in events]
        matrix = self.hasher.transform(feature_dicts)
        self.global_model.fit(matrix)
        self.entity_baseline.fit(events)
        self._fitted = True

    def score_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self._fitted:
            raise ValueError("EntityAnomalyEnsemble must be fitted before scoring")

        feature_dict = build_behavioral_hash_features(event)
        matrix = self.hasher.transform([feature_dict])
        raw_global = float(-self.global_model.score_samples(matrix)[0])
        normalized_global = max(0.0, min(raw_global / 2.0, 1.0))

        entity_result = self.entity_baseline.score_event(event)
        final_score = (normalized_global * 0.55) + (float(entity_result["aggregate_score"]) * 0.45)
        return {
            "global_score_raw": raw_global,
            "global_score": round(normalized_global, 4),
            "entity_score": entity_result["aggregate_score"],
            "entity_breakdown": entity_result["entity_scores"],
            "label": "anomalous" if final_score >= 0.6 else "normal",
            "final_score": round(final_score, 4),
        }

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "hasher": self.hasher,
                "global_model": self.global_model,
                "entity_baseline": self.entity_baseline,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> "EntityAnomalyEnsemble":
        payload = joblib.load(path)
        instance = cls()
        instance.hasher = payload["hasher"]
        instance.global_model = payload["global_model"]
        instance.entity_baseline = payload["entity_baseline"]
        instance._fitted = True
        return instance
