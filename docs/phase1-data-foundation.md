# Phase 1 Data Foundation

Phase 1 establishes the data contract and experiment baseline for TrustSphere.

## Scope

This phase includes:

- complete dataset registry for all shared sources
- canonical event schema
- deterministic split generation
- manifest creation for dataset lineage

## Included datasets

### Primary

- `cybersecurity_threat_detection_logs.csv`

### Auxiliary bundle

- `Nazario_5.zip`

### Auxiliary members

- `Nazario_5.csv`
- `email_text.csv`
- `Website Phishing.csv`
- `5.urldata.csv`
- `dataset.arff`
- `test_email_dataset.csv`
- `test_email_dataset - Copy.csv`

## Design decisions

- Large raw data stays outside the repository.
- The dataset registry stores absolute source paths for now because those are the actual files currently available.
- Splits are hash-based so they are deterministic and do not require loading the full 6 million row dataset into memory.
- The archive bundle is cataloged separately and each member dataset is registered independently.

## Why this matters

The surprise evaluation will mutate schemas, formats, timestamps, and signal quality. If data lineage and contracts are weak, later model work becomes fragile. This phase makes the system reproducible before we start training and normalization logic.
