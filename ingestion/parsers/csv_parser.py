from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator


def parse_csv_file(path: str | Path) -> Iterator[dict[str, str]]:
    csv.field_size_limit(10_000_000)
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield dict(row)
