# Phase 3 Prefiltering

Phase 3 adds a multi-stage prefiltering pipeline for cyber incident logs.

## Implemented stages

1. Rule-based scoring and initial label assignment
2. Supervised first-stage classifier using the 6M-row network log dataset
3. Behavioral anomaly scoring with Isolation Forest
4. Final decision fusion to produce `true_positive`, `false_positive`, or `uncertain`

## Main files

- [prefiltering/rules/risk_rules.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prefiltering/rules/risk_rules.py)
- [prefiltering/ml/feature_extractor.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prefiltering/ml/feature_extractor.py)
- [prefiltering/ml/supervised_model.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prefiltering/ml/supervised_model.py)
- [anomaly_detection/models/behavioral_anomaly_model.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/anomaly_detection/models/behavioral_anomaly_model.py)
- [prefiltering/fusion/decision_fusion.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prefiltering/fusion/decision_fusion.py)
- [prefiltering/pipeline.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prefiltering/pipeline.py)
- [scripts/train_prefilter_models.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/scripts/train_prefilter_models.py)

## Training approach

- The primary classifier uses streaming `partial_fit` training so it can scale to the 6M-row dataset.
- Label mapping for the main dataset is:
  - `malicious -> true_positive`
  - `suspicious -> uncertain`
  - `benign -> false_positive`
- Auxiliary email and phishing classifiers are trained separately and saved as optional sidecar models.
- The anomaly detector is trained from benign-heavy rows to surface unusual behavior beyond the first-stage classifier.
