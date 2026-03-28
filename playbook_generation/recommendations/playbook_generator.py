from __future__ import annotations

import json
from typing import Any

from llm_service.client.client_factory import build_llm_client
from llm_service.prompts.playbook_prompt import build_playbook_messages
from playbook_generation.serializers.evidence_serializer import serialize_incident_for_llm
from playbook_generation.templates.playbook_schema import PLAYBOOK_SCHEMA
from prioritization.ranking.prioritize_incidents import llm_candidate_incidents


def _fallback_playbook(evidence_package: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "summary": f"LLM unavailable: {reason}",
        "likely_attack_path": "Insufficient model output; use structured evidence directly.",
        "confidence_rationale": "Fallback generated because the LLM request failed or returned invalid JSON.",
        "recommended_actions": [
            {
                "title": "Review structured evidence and confirm impact scope",
                "rationale": "The automated playbook could not be generated reliably.",
                "approval_required": True,
                "priority": "high"
            }
        ],
        "containment_checks": [
            "Validate affected assets and accounts from the incident entity list.",
            "Confirm whether any blocking or containment already occurred upstream."
        ],
        "escalation_conditions": [
            "Escalate if critical assets are involved.",
            "Escalate if additional related incidents appear."
        ],
        "playbook_status": "fallback"
    }


def _validate_playbook_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for key in PLAYBOOK_SCHEMA["required_keys"]:
        payload.setdefault(key, [] if key.endswith("s") else "")
    actions = payload.get("recommended_actions", [])
    normalized_actions = []
    for action in actions:
        normalized = {field: action.get(field) for field in PLAYBOOK_SCHEMA["required_action_keys"]}
        normalized["approval_required"] = True
        normalized_actions.append(normalized)
    payload["recommended_actions"] = normalized_actions
    payload["audience"] = "analyst_only"
    payload["approval_mode"] = "human_approval_required"
    return payload


def generate_playbook_for_incident(priority_record: dict[str, Any], provider: str | None = None) -> dict[str, Any]:
    evidence_package = serialize_incident_for_llm(priority_record)
    client = build_llm_client(provider=provider)
    response = client.generate(build_playbook_messages(evidence_package))
    if response.status != "ok" or response.parsed_json is None:
        playbook = _fallback_playbook(evidence_package, response.raw_text)
    else:
        playbook = _validate_playbook_payload(response.parsed_json)
    return {
        "incident_id": priority_record["incident_id"],
        "provider": response.provider,
        "llm_status": response.status,
        "analyst_only": True,
        "approval_required": True,
        "evidence_package": evidence_package,
        "playbook": playbook,
    }


def generate_candidate_playbooks(priority_records: list[dict[str, Any]], provider: str | None = None) -> list[dict[str, Any]]:
    outputs = []
    for record in llm_candidate_incidents(priority_records):
        outputs.append(generate_playbook_for_incident(record, provider=provider))
    return outputs
