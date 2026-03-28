from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

VENDOR_DIR = Path(__file__).resolve().parents[2] / ".vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import joblib
from sklearn.feature_extraction import FeatureHasher
from sklearn.naive_bayes import MultinomialNB

from prefiltering.ml.feature_extractor import build_features_for_dataset
from prefiltering.ml.labels import map_dataset_label


CLASSES = ["false_positive", "uncertain", "true_positive"]
@dataclass(slots=True)
class ClassifierPrediction:
    label: str
    probabilities: dict[str, float]


class StreamingEventClassifier:
    def __init__(self, n_features: int = 2**18) -> None:
        self.dataset_id: str | None = None
        self.hasher = FeatureHasher(n_features=n_features, input_type="dict", alternate_sign=False)
        self.model = MultinomialNB(alpha=0.05)
        self._initialized = False

    def set_dataset(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id

    def partial_fit(self, rows: list[dict[str, Any]], labels: list[str]) -> None:
        if not rows:
            return
        if not self.dataset_id:
            raise ValueError("dataset_id must be set before training")
        feature_dicts = [build_features_for_dataset(self.dataset_id, row) for row in rows]
        matrix = self.hasher.transform(feature_dicts)
        if not self._initialized:
            self.model.partial_fit(matrix, labels, classes=CLASSES)
            self._initialized = True
            return
        self.model.partial_fit(matrix, labels)

    def train_from_rows(self, dataset_id: str, rows: list[dict[str, Any]], raw_label_field: str) -> int:
        self.set_dataset(dataset_id)
        usable_rows: list[dict[str, Any]] = []
        labels: list[str] = []
        for row in rows:
            mapped = map_dataset_label(dataset_id, row.get(raw_label_field))
            if mapped is None:
                continue
            usable_rows.append(row)
            labels.append(mapped)
        self.partial_fit(usable_rows, labels)
        return len(usable_rows)

    def predict(self, dataset_id: str, row: dict[str, Any]) -> ClassifierPrediction:
        feature_dict = build_features_for_dataset(dataset_id, row)
        matrix = self.hasher.transform([feature_dict])
        probabilities = self.model.predict_proba(matrix)[0]
        payload = {label: float(prob) for label, prob in zip(self.model.classes_, probabilities)}
        label = max(payload, key=payload.get)
        return ClassifierPrediction(label=label, probabilities=payload)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"hasher": self.hasher, "model": self.model}, path)

    @classmethod
    def load(cls, path: str | Path) -> "StreamingEventClassifier":
        payload = joblib.load(path)
        instance = cls()
        instance.hasher = payload["hasher"]
        instance.model = payload["model"]
        instance._initialized = True
        return instance
