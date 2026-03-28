from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator


SYSLOG_PATTERN = re.compile(
    r"^(?:<(?P<priority>\d+)>)?"
    r"(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<app>[A-Za-z0-9_.-]+?)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)

KV_PATTERN = re.compile(r"(?P<key>[A-Za-z0-9_.-]+)=(?P<value>\"[^\"]*\"|\S+)")


def _parse_kv_pairs(message: str) -> dict[str, str]:
    extracted: dict[str, str] = {}
    for match in KV_PATTERN.finditer(message):
        value = match.group("value")
        extracted[match.group("key")] = value.strip('"')
    return extracted


def parse_syslog_file(path: str | Path) -> Iterator[dict[str, str]]:
    with open(path, "r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            raw_line = line.rstrip("\n")
            if not raw_line.strip():
                continue
            match = SYSLOG_PATTERN.match(raw_line)
            if not match:
                yield {
                    "raw_message": raw_line,
                    "parser_status": "unparsed",
                    "line_number": str(index),
                }
                continue
            payload = match.groupdict(default="")
            payload["raw_message"] = raw_line
            payload["line_number"] = str(index)
            payload.update(_parse_kv_pairs(payload.get("message", "")))
            yield payload
