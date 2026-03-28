from __future__ import annotations

PLAYBOOK_SCHEMA = {
    "required_keys": [
        "incident_summary",
        "evidence_panel",
        "risk_score",
        "risk_breakdown",
        "confidence_level",
        "confidence_rationale",
        "attack_stage",
        "recommended_actions",
        "approval_requirement",
        "business_impact",
        "explainability",
    ],
    "required_action_keys": [
        "title",
        "impact",
        "approval_required",
        "priority",
    ],
    "required_evidence_keys": [
        "signal",
        "observation",
        "risk_contribution",
    ],
    "required_risk_breakdown_keys": [
        "factor",
        "score",
    ],
}
