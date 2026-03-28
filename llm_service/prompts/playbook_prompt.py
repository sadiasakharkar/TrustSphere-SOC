from __future__ import annotations

import json
from typing import Any


SYSTEM_INSTRUCTIONS = """
You are TrustSphere's offline cyber incident reasoning assistant.
Only use the structured evidence provided.
Do not invent telemetry, actions, or certainty.
All remediation steps must be analyst approval required.
Respond strictly as JSON with keys:
incident_summary, evidence_panel, risk_score, risk_breakdown, confidence_level,
confidence_rationale, attack_stage, recommended_actions, approval_requirement,
business_impact, explainability.
evidence_panel must be a list of objects with keys: signal, observation, risk_contribution.
risk_score must be an object with keys: score, label.
risk_breakdown must be a list of objects with keys: factor, score.
confidence_level must be an object with keys: level, score.
attack_stage must be a short string describing attack lifecycle stage.
recommended_actions must be a list of objects with keys:
title, impact, approval_required, priority.
business_impact must be a list of short strings.
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
