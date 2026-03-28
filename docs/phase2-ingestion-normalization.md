# Phase 2 Ingestion And Normalization

Phase 2 adds the first operational pipeline layer on top of the Phase 1 data foundation.

## Included capabilities

- ingestion for `CSV`, `JSON`, `NDJSON`, and `syslog-like` files
- heterogeneous field alias mapping into the canonical event schema
- missing field tolerance
- timestamp cleanup into UTC ISO format
- PS1-style disruption generation for mixed and degraded inputs

## Main entry points

- [ingestion/loaders/file_loader.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/ingestion/loaders/file_loader.py)
- [ingestion/adapters/normalize_records.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/ingestion/adapters/normalize_records.py)
- [normalization/mappers/canonical_mapper.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/normalization/mappers/canonical_mapper.py)
- [scripts/generate_ps1_disruptions.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/scripts/generate_ps1_disruptions.py)

## Notes

- The syslog parser is intentionally tolerant and extracts key-value pairs from the message body.
- Missing timestamps fall back to the current UTC time so normalization does not fail hard.
- Unknown fields are preserved inside `artifacts.feature_map` instead of being dropped.
- The disruption generator intentionally introduces renamed fields, dropped attributes, duplicates, noise, and timestamp disorder.
