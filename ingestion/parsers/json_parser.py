from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator


def parse_json_file(path: str | Path) -> Iterator[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8")
    payload = _load_json_or_sequence(text)
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return
    if isinstance(payload, dict):
        for key in ("events", "records", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return
        yield payload


def parse_ndjson_file(path: str | Path) -> Iterator[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                yield payload


def _load_json_or_sequence(text: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Tolerate "object, object, object" JSON fragments by wrapping them into a list.
    candidate = f"[{stripped.rstrip(',')}]"
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    objects: list[dict[str, Any]] = []
    decoder = json.JSONDecoder()
    index = 0
    while index < len(stripped):
        while index < len(stripped) and stripped[index] in " \r\n\t,":
            index += 1
        if index >= len(stripped):
            break
        obj, offset = decoder.raw_decode(stripped, index)
        if isinstance(obj, dict):
            objects.append(obj)
        index = offset
    if objects:
        return objects
    raise json.JSONDecodeError("Unable to parse JSON content", stripped, 0)
