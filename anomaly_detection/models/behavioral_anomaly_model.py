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

from prefiltering.ml.feature_extractor import build_features_for_dataset


class BehavioralAnomalyDetector:
    def __init__(self, n_features: int = 2**16, contamination: float = 0.08, n_estimators: int = 150) -> None:
        self.dataset_id: str | None = None
        self.hasher = FeatureHasher(n_features=n_features, input_type="dict", alternate_sign=False)
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
            n_jobs=1,
        )
        self._fitted = False

    def fit(self, dataset_id: str, rows: list[dict[str, Any]]) -> None:
        self.dataset_id = dataset_id
        feature_dicts = [build_features_for_dataset(dataset_id, row) for row in rows]
        matrix = self.hasher.transform(feature_dicts)
        self.model.fit(matrix)
        self._fitted = True

    def score(self, dataset_id: str, row: dict[str, Any]) -> dict[str, float | str]:
        if not self._fitted:
            raise ValueError("Anomaly detector must be fitted before scoring")
        feature_dict = build_features_for_dataset(dataset_id, row)
        matrix = self.hasher.transform([feature_dict])
        raw_score = float(-self.model.score_samples(matrix)[0])
        normalized = max(0.0, min(raw_score / 2.0, 1.0))
        label = "anomalous" if normalized >= 0.6 else "normal"
        return {
            "raw_score": raw_score,
            "normalized_score": normalized,
            "label": label,
        }

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"hasher": self.hasher, "model": self.model}, path)

    @classmethod
    def load(cls, path: str | Path) -> "BehavioralAnomalyDetector":
        payload = joblib.load(path)
        instance = cls()
        instance.hasher = payload["hasher"]
        instance.model = payload["model"]
        instance._fitted = True
        return instance
