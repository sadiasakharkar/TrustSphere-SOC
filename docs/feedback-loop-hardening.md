# Feedback Loop And Hardening

This layer closes the loop between analyst decisions, ranking adjustments, retraining signals, and PS1 disruption validation.

## Implemented capabilities

- analyst feedback capture for true/false positive verdicts
- playbook usefulness feedback capture
- feedback-based score adjustment during incident prioritization
- retraining example export for future model updates
- PS1 disruption validation across CSV, JSON, and syslog variants

## Main files

- [feedback_loop/analyst_feedback/feedback_store.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/feedback_loop/analyst_feedback/feedback_store.py)
- [feedback_loop/retraining_signals/signal_builder.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/feedback_loop/retraining_signals/signal_builder.py)
- [feedback_loop/retraining_signals/retraining_dataset.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/feedback_loop/retraining_signals/retraining_dataset.py)
- [scripts/record_analyst_feedback.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/scripts/record_analyst_feedback.py)
- [scripts/export_retraining_signals.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/scripts/export_retraining_signals.py)
- [scripts/validate_ps1_baseline.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/scripts/validate_ps1_baseline.py)

## Current behavior

- feedback can boost or suppress similar future incidents during prioritization
- feedback can be exported into JSONL retraining examples
- PS1 baseline validation confirms that the pipeline still produces incidents and ranked outputs across heterogeneous disrupted formats
