# Canonical Event Schema

This folder defines the Phase 1 canonical event contract used across ingestion, normalization, prefiltering, anomaly detection, and later LLM reasoning.

## Why this exists

The PS1 surprise condition requires the system to survive:

- mixed log formats
- renamed fields
- missing attributes
- duplicate alerts
- noisy inputs
- timestamp disorder

That only works if every source eventually lands in one durable representation.

## Current schema

The JSON schema file is stored at [canonical_event_schema.json](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/normalization/schema/canonical_event_schema.json).

The current model keeps:

- source lineage
- timing
- security principals
- artifact fields
- labels
- raw data references

This is intentionally broad enough to include the current network, email, and phishing datasets without locking us into one vendor format.
