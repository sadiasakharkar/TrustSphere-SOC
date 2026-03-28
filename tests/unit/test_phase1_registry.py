from pathlib import Path

from shared.types.dataset_registry import load_dataset_registry


def test_registry_loads_all_datasets() -> None:
    registry_path = Path("configs/dataset_registry.json")
    specs = load_dataset_registry(registry_path)
    ids = {spec.id for spec in specs}

    assert "cyber_threat_logs_v1" in ids
    assert "nazario_bundle_v1" in ids
    assert "email_text_v1" in ids
    assert "phishing_arff_v1" in ids
    assert len(specs) == 9
