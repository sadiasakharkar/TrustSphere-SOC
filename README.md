# TrustSphere-SOC

TrustSphere-SOC is an offline-first SOC intelligence platform for ingesting heterogeneous security telemetry, normalizing it into a common event model, prioritizing incidents, and generating analyst-only playbooks.

This repository currently includes the Phase 1 data foundation:

- a canonical event schema for all downstream modules
- a registry covering every dataset shared so far
- deterministic dataset split generation
- metadata and manifest generation for repeatable experiments

## Current focus

Phase 1 is designed to make the rest of the pipeline reliable:

1. register every available dataset
2. define one canonical event contract
3. generate reproducible train/validation/test splits
4. keep large raw data outside Git while still making the repo runnable

## Quick start

1. Review and adjust dataset paths in [configs/dataset_registry.json](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/configs/dataset_registry.json).
2. Run:

```powershell
python scripts/prepare_phase1_data.py
```

3. Generated manifests and split files will appear under `datasets/processed/`.

## Dataset coverage

The current registry includes all provided data sources:

- `cybersecurity_threat_detection_logs.csv`
- `Nazario_5.zip`
- `Nazario_5.csv`
- `5.urldata.csv`
- `dataset.arff`
- `Website Phishing.csv`
- `email_text.csv`
- `test_email_dataset.csv`
- `test_email_dataset - Copy.csv`

## Phase 1 outputs

- canonical schema definition
- source and dataset registry
- deterministic splits for tabular datasets
- manifest files with row counts, labels, hashes, and lineage

## Notes

- Raw datasets are intentionally not committed because of size.
- The prep script reads the external source files directly from their current absolute paths.
- When we move into Phase 2, these manifests become the contract for ingestion and normalization.
