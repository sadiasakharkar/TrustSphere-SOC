# Incident Prioritization

This layer ranks incidents, not raw alerts, and decides which incidents are strong enough to send to the LLM.

## Signals combined

- prefilter confidence
- anomaly score
- incident severity
- recurrence
- asset context
- incident confidence

## Main files

- [prioritization/ranking/prioritize_incidents.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prioritization/ranking/prioritize_incidents.py)
- [prioritization/risk_engine/asset_context.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prioritization/risk_engine/asset_context.py)
- [prioritization/models/priority_record.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/prioritization/models/priority_record.py)
- [configs/asset_context.json](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/configs/asset_context.json)

## Current policy

- `critical` and `high` priority incidents float to the top
- only incidents above the configured priority and confidence thresholds are marked `llm_eligible`
- asset context boosts incidents that touch sensitive IPs, hosts, or request paths

## Next improvement

The next step after this should be wiring actual prefilter and anomaly outputs into the incident evidence bundle automatically so the ranking uses live pipeline scores instead of defaults.
