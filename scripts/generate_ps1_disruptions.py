from __future__ import annotations

import csv
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.parsers.csv_parser import parse_csv_file


FIELD_RENAMES = {
    "timestamp": "event_time",
    "source_ip": "src_ip",
    "dest_ip": "destination_ip",
    "protocol": "proto",
    "action": "decision",
    "threat_label": "classification",
    "log_type": "event_category",
    "bytes_transferred": "bytes_out",
    "user_agent": "ua",
    "request_path": "uri",
}


def _drop_random_fields(record: dict[str, str], rng: random.Random) -> dict[str, str]:
    output = dict(record)
    for key in list(output):
        if rng.random() < 0.18:
            output.pop(key, None)
    return output


def _rename_fields(record: dict[str, str], rng: random.Random) -> dict[str, str]:
    output: dict[str, str] = {}
    for key, value in record.items():
        if key in FIELD_RENAMES and rng.random() < 0.65:
            output[FIELD_RENAMES[key]] = value
        else:
            output[key] = value
    return output


def _shuffle_timestamp(record: dict[str, str], rng: random.Random) -> dict[str, str]:
    output = dict(record)
    timestamp = output.get("timestamp") or output.get("event_time")
    if not timestamp:
        return output
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return output
    shifted = parsed + timedelta(minutes=rng.randint(-240, 240))
    field_name = "event_time" if "event_time" in output else "timestamp"
    output[field_name] = shifted.isoformat()
    return output


def _noise_record(rng: random.Random) -> dict[str, str]:
    return {
        "event_time": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
        "src_ip": f"10.0.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        "destination_ip": f"172.16.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
        "proto": rng.choice(["TCP", "UDP", "HTTP", "HTTPS"]),
        "decision": rng.choice(["allowed", "blocked"]),
        "classification": rng.choice(["benign", "suspicious"]),
        "event_category": rng.choice(["firewall", "application", "ids"]),
        "bytes_out": str(rng.randint(64, 50000)),
        "ua": rng.choice(["curl/7.64.1", "Mozilla/5.0", "Nmap Scripting Engine"]),
        "uri": rng.choice(["/", "/login", "/admin/config"]),
        "synthetic_noise": "true",
    }


def _to_syslog(record: dict[str, str], host: str) -> str:
    timestamp = record.get("event_time") or record.get("timestamp") or datetime.utcnow().isoformat()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        rendered_ts = parsed.strftime("%b %d %H:%M:%S")
    except ValueError:
        rendered_ts = "Jan 01 00:00:00"
    message_parts = [f"{key}={value}" for key, value in record.items() if value not in (None, "")]
    return f"<134>{rendered_ts} {host} trustsphere-agent[1001]: {' '.join(message_parts)}"


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/generate_ps1_disruptions.py <input_csv> <output_dir> [row_limit]")
        raise SystemExit(1)

    input_csv = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    row_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 250
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    selected_rows = []
    for index, row in enumerate(parse_csv_file(input_csv), start=1):
        selected_rows.append(row)
        if index >= row_limit:
            break

    disrupted = []
    for row in selected_rows:
        mutated = _rename_fields(row, rng)
        mutated = _drop_random_fields(mutated, rng)
        mutated = _shuffle_timestamp(mutated, rng)
        disrupted.append(mutated)
        if rng.random() < 0.12:
            disrupted.append(dict(mutated))
        if rng.random() < 0.10:
            disrupted.append(_noise_record(rng))

    rng.shuffle(disrupted)

    csv_rows = disrupted[:]
    json_rows = disrupted[:]
    syslog_rows = [_to_syslog(row, host=f"soc-node-{rng.randint(1, 3)}") for row in disrupted]

    csv_fieldnames = sorted({key for row in csv_rows for key in row})
    with (output_dir / "ps1_disrupted.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    (output_dir / "ps1_disrupted.json").write_text(
        json.dumps({"events": json_rows}, indent=2),
        encoding="utf-8",
    )
    (output_dir / "ps1_disrupted.syslog").write_text(
        "\n".join(syslog_rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
