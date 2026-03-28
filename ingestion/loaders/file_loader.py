from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from ingestion.parsers.csv_parser import parse_csv_file
from ingestion.parsers.json_parser import parse_json_file, parse_ndjson_file
from ingestion.parsers.syslog_parser import parse_syslog_file


SUPPORTED_EXTENSIONS = {
    ".csv": parse_csv_file,
    ".json": parse_json_file,
    ".ndjson": parse_ndjson_file,
    ".syslog": parse_syslog_file,
    ".log": parse_syslog_file,
}


def load_records(path: str | Path) -> Iterator[dict[str, Any]]:
    resolved = Path(path)
    suffix = resolved.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    yield from SUPPORTED_EXTENSIONS[suffix](resolved)
