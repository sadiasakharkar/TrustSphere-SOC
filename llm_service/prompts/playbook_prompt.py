from __future__ import annotations

import json
from typing import Any


SYSTEM_INSTRUCTIONS = """
You are TrustSphere's offline cyber incident reasoning assistant.
Only use the structured evidence provided.
Do not invent telemetry, actions, or certainty.
All remediation steps must be analyst approval required.
Respond strictly as JSON with keys:
incident_summary, confidence_rationale, recommended_actions, explainability.
Do not rewrite or replace the evidence panel, risk score, risk breakdown, confidence level,
attack stage, approval requirement, or business impact because those are computed deterministically.
incident_summary must be 1-2 short sentences.
confidence_rationale must be a list of short evidence-backed reasons.
recommended_actions must be a list of objects with keys:
title, impact, approval_required, priority.
explainability must be 2-4 sentences in plain language.
If you are unsure, return empty arrays/strings rather than inventing details.
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
