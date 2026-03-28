from __future__ import annotations

import json
from typing import Any


SYSTEM_INSTRUCTIONS = """
You are TrustSphere's offline cyber incident reasoning assistant.
Only use the structured evidence provided.
Do not invent telemetry, actions, or certainty.
All remediation steps must be analyst approval required.
Respond strictly as JSON with keys:
summary, likely_attack_path, confidence_rationale, recommended_actions, containment_checks, escalation_conditions.
recommended_actions must be a list of objects with keys:
title, rationale, approval_required, priority.
containment_checks must be a list of short strings.
escalation_conditions must be a list of short strings.
""".strip()


def build_playbook_messages(evidence_package: dict[str, Any]) -> list[dict[str, str]]:
    user_payload = {
        "task": "Generate an analyst-only incident response playbook from structured evidence.",
        "constraints": [
            "Use only the supplied structured evidence.",
            "Do not recommend auto-remediation.",
            "Every action must require human approval.",
            "Prefer precise, evidence-backed steps."
        ],
        "incident": evidence_package,
    }
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]
