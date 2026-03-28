# Entity Behavior Anomaly Detection

This layer extends anomaly detection beyond row-level scoring and models entity behavior across:

- users
- source IPs
- destination IPs
- hosts
- protocols
- actions
- time-of-day and day-of-week
- data transfer volume
- request path patterns

## Components

- [anomaly_detection/feature_engineering/behavioral_features.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/anomaly_detection/feature_engineering/behavioral_features.py)
- [anomaly_detection/models/entity_baseline_model.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/anomaly_detection/models/entity_baseline_model.py)
- [anomaly_detection/models/entity_anomaly_ensemble.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/anomaly_detection/models/entity_anomaly_ensemble.py)
- [anomaly_detection/scoring/entity_behavior_scorer.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/anomaly_detection/scoring/entity_behavior_scorer.py)

## Approach

The ensemble combines:

1. a global Isolation Forest over hashed behavioral features
2. an entity-baseline model that scores deviation from known user/IP/host/protocol/action patterns

This gives us both:

- broad anomaly sensitivity across many dimensions
- interpretable per-entity anomaly breakdowns

## Training modes

- `benign_only=true`: semi-supervised baseline learning from likely-normal traffic
- `benign_only=false`: unsupervised training over all normalized events

## Scripts

- Train:
  `python scripts/train_entity_anomaly_models.py 200000 true`
- Demo:
  `python scripts/run_entity_anomaly_demo.py artifacts/anomaly_detection/entity_anomaly_ensemble.joblib tests/fixtures/sample_events.csv cyber_threat_logs_v1 network_security 2`
