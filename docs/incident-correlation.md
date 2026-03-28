# Correlation And Incident Building

This layer takes normalized events and turns them into analyst-ready incidents.

## Implemented capabilities

- merge duplicate alerts inside a configurable time window
- group related events into incidents using shared entities and activity shape
- reconstruct ordered timelines even when source timestamps arrive shuffled
- build evidence bundles for incident review and downstream playbook generation

## Main components

- [correlation/entity_resolution/deduplicator.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/correlation/entity_resolution/deduplicator.py)
- [correlation/incident_builder.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/correlation/incident_builder.py)
- [correlation/timeline_reconstruction/timeline_builder.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/correlation/timeline_reconstruction/timeline_builder.py)
- [correlation/attack_graph/evidence_bundle.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/correlation/attack_graph/evidence_bundle.py)
- [correlation/models/incident.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/correlation/models/incident.py)

## Current correlation logic

The current incident grouping uses:

- source IP
- destination IP
- user/email identity when present
- protocol
- action
- event kind

This is a good first correlation layer for v1. Later we can extend it with:

- sliding time windows
- causality edges
- MITRE stage transitions
- attack graph expansion across multiple tools
