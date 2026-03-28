from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Iterator


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def parse_xlsx_file(path: str | Path) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = _load_shared_strings(archive)
        sheet_xml = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = sheet_xml.findall(".//a:sheetData/a:row", NS)
        if not rows:
            return
        header_cells = _extract_row(rows[0], shared_strings)
        headers = [cell.strip() for cell in header_cells if cell is not None]
        for row in rows[1:]:
            values = _extract_row(row, shared_strings)
            if not any(value for value in values):
                continue
            record = _row_to_record(headers, values)
            if record:
                yield record


def _load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings: list[str] = []
    for item in shared_root.findall("a:si", NS):
        text = "".join(node.text or "" for node in item.findall(".//a:t", NS))
        strings.append(text)
    return strings


def _column_index(cell_ref: str) -> int:
    letters = "".join(char for char in cell_ref if char.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - 64)
    return max(index - 1, 0)


def _extract_row(row: ET.Element, shared_strings: list[str]) -> list[str]:
    cells = row.findall("a:c", NS)
    values: list[str] = []
    current_index = 0
    for cell in cells:
        cell_ref = cell.get("r", "")
        target_index = _column_index(cell_ref) if cell_ref else current_index
        while len(values) < target_index:
            values.append("")
        value = ""
        value_node = cell.find("a:v", NS)
        if value_node is not None and value_node.text is not None:
            if cell.get("t") == "s":
                try:
                    value = shared_strings[int(value_node.text)]
                except (ValueError, IndexError):
                    value = value_node.text
            else:
                value = value_node.text
        values.append(value)
        current_index = target_index + 1
    return values


def _row_to_record(headers: list[str], values: list[str]) -> dict[str, str]:
    record: dict[str, str] = {}
    limit = min(len(headers), len(values))
    for index in range(limit):
        header = headers[index]
        value = values[index]
        if header:
            record[header] = value

    # Handle the malformed PS-1 spreadsheet rows by backfilling missing columns from shifted values.
    if "message" not in record and len(values) >= 7:
        if "severity" in record and record.get("severity") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            record["message"] = record["severity"]
        if "ip" in record and not _looks_like_ip(record.get("ip", "")) and ":" not in record.get("ip", ""):
            record["notes"] = record["ip"]
        if "file" in record and not record.get("file"):
            record["file"] = values[7] if len(values) > 7 else ""
        if "notes" not in record and values:
            record["notes"] = values[-1]
    return {key: value for key, value in record.items() if value != ""}


def _looks_like_ip(value: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", value))
