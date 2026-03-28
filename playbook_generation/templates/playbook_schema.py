from __future__ import annotations

PLAYBOOK_SCHEMA = {
    "required_keys": [
        "summary",
        "likely_attack_path",
        "confidence_rationale",
        "recommended_actions",
        "containment_checks",
        "escalation_conditions"
    ],
    "required_action_keys": [
        "title",
        "rationale",
        "approval_required",
        "priority"
    ]
}
