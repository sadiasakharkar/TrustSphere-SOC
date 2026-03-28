from scripts.prepare_phase1_data import fingerprint_row, split_name_from_hash


def test_split_is_stable_for_same_row() -> None:
    row = {"timestamp": "2024-01-01T00:00:00", "source_ip": "1.1.1.1", "dest_ip": "2.2.2.2"}
    first = fingerprint_row(row, ["timestamp", "source_ip", "dest_ip"])
    second = fingerprint_row(row, ["timestamp", "source_ip", "dest_ip"])

    assert first == second
    assert split_name_from_hash(first) == split_name_from_hash(second)


def test_split_name_is_valid() -> None:
    result = split_name_from_hash("0" * 64)
    assert result in {"train", "validation", "test"}
