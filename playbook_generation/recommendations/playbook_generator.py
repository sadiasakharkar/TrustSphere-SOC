from __future__ import annotations

from typing import Any

from llm_service.client.client_factory import build_llm_client
from llm_service.prompts.playbook_prompt import build_playbook_messages
from playbook_generation.serializers.evidence_serializer import serialize_incident_for_llm
from playbook_generation.templates.playbook_schema import PLAYBOOK_SCHEMA
from prioritization.ranking.prioritize_incidents import llm_candidate_incidents


def _evidence_text(evidence: dict[str, Any]) -> str:
    artifacts = evidence.get("artifacts", {})
    parts = [
        str(artifacts.get("action") or ""),
        str(artifacts.get("request_path") or ""),
        str(artifacts.get("body") or ""),
        str(artifacts.get("feature_map") or ""),
    ]
    return " ".join(parts).lower()


def _risk_label(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _confidence_level(score: float) -> str:
    if score >= 85:
        return "HIGH"
    if score >= 65:
        return "MEDIUM"
    return "LOW"


def _attack_stage(evidence_package: dict[str, Any]) -> str:
    timeline = evidence_package.get("timeline", [])
    combined = " ".join(str(item.get("action") or "").lower() for item in timeline)
    if "sign-in" in combined or "login" in combined:
        if "new-inboxrule" in combined or "mailitemsaccessed" in combined or "send" in combined:
            return "Initial Access -> Credential Abuse"
        return "Initial Access Suspected"
    if "process_create" in combined or "powershell" in combined or "cmd.exe" in combined:
        return "Execution -> Command Execution"
    if "file_write" in combined or "vss_delete" in combined:
        return "Impact / Collection Suspected"
    if "net_conn" in combined or "access_denied" in combined:
        return "Lateral Movement Suspected"
    return "Investigation In Progress"


def _build_evidence_panel(evidence_package: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    structured = evidence_package.get("structured_evidence", [])
    for evidence in structured:
        text = _evidence_text(evidence)
        principal = evidence.get("principal", {})
        feature_map = evidence.get("artifacts", {}).get("feature_map", {})
        if "suspiciousipaddress" in text or "unfamiliarfeatures" in text:
            entries.append(
                {
                    "signal": "Login risk indicators",
                    "observation": f"Risk events flagged for {principal.get('user_id') or 'account'} from {principal.get('src_ip') or 'unknown source'}.",
                    "risk_contribution": 30,
                }
            )
        if "new-inboxrule" in text or "forwardto" in text or "deletemessage" in text:
            entries.append(
                {
                    "signal": "Mailbox forwarding rule",
                    "observation": "Inbox rule configured to forward or hide sensitive messages.",
                    "risk_contribution": 20,
                }
            )
        if "mailitemsaccessed" in text:
            entries.append(
                {
                    "signal": "Mailbox access burst",
                    "observation": "Sensitive mailbox content was accessed after the risky sign-in.",
                    "risk_contribution": 15,
                }
            )
        if "filedownloaded" in text:
            entries.append(
                {
                    "signal": "Document download activity",
                    "observation": "User downloaded internal files after the suspicious sequence began.",
                    "risk_contribution": 15,
                }
            )
        if "send" in text:
            entries.append(
                {
                    "signal": "Outbound message activity",
                    "observation": "Outgoing email activity followed the risky access pattern.",
                    "risk_contribution": 10,
                }
            )
        if "xp_cmdshell" in text or "sp_configure" in text:
            entries.append(
                {
                    "signal": "SQL injection / command execution pattern",
                    "observation": "Request path contains database command-execution indicators.",
                    "risk_contribution": 30,
                }
            )
        if "cmd.exe" in text and "sqlservr.exe" in text:
            entries.append(
                {
                    "signal": "Service-spawned shell",
                    "observation": "Database service lineage spawned command shell execution.",
                    "risk_contribution": 35,
                }
            )
        if "login_fail" in text:
            attempts = feature_map.get("attempts")
            attempt_text = f"{attempts} failed attempts" if attempts else "Repeated login failures detected"
            entries.append(
                {
                    "signal": "Authentication failure pattern",
                    "observation": attempt_text,
                    "risk_contribution": 20,
                }
            )
        if "file_write" in text or "vss_delete" in text:
            entries.append(
                {
                    "signal": "Potential destructive file activity",
                    "observation": "File system activity is consistent with impact or staging behavior.",
                    "risk_contribution": 20,
                }
            )

    if not entries:
        for evidence in structured[:3]:
            artifacts = evidence.get("artifacts", {})
            entries.append(
                {
                    "signal": str(artifacts.get("action") or "Observed activity"),
                    "observation": f"Observed at {evidence.get('event_time')} with severity {evidence.get('severity')}.",
                    "risk_contribution": 10,
                }
            )
    return entries[:5]


def _build_risk_breakdown(evidence_package: dict[str, Any], evidence_panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = evidence_package.get("summary", {})
    reasons = " ".join(evidence_package.get("priority", {}).get("reasons", [])).lower()
    event_count = int(summary.get("event_count", 0))
    anomaly_score = float(summary.get("average_anomaly_score", 0.0))
    behavior = min(40, 10 + (event_count * 5) + int(anomaly_score * 10))
    threat = 30 if "risky" in reasons or "exploit" in reasons or "suspicious" in reasons else 18
    evidence = min(30, sum(item["risk_contribution"] for item in evidence_panel[:3]) // 3)
    total = behavior + threat + evidence
    if total == 0:
        return [{"factor": "Evidence confidence", "score": 15}]
    scale = 100 / total
    normalized = [
        {"factor": "Behavior anomaly", "score": round(behavior * scale)},
        {"factor": "Threat pattern match", "score": round(threat * scale)},
        {"factor": "Evidence correlation", "score": round(evidence * scale)},
    ]
    return normalized


def _build_recommended_actions(evidence_package: dict[str, Any]) -> list[dict[str, Any]]:
    entities = evidence_package.get("entities", {})
    users = entities.get("users", [])
    hosts = entities.get("hosts", [])
    actions = []
    if users:
        actions.append(
            {
                "title": f"Temporarily lock account: {users[0]}",
                "impact": "Prevents continued attacker access and stops further misuse of the identity.",
                "approval_required": True,
                "priority": "high",
            }
        )
    if hosts:
        actions.append(
            {
                "title": f"Isolate host: {hosts[0]}",
                "impact": "Contains local execution or lateral movement from the affected endpoint.",
                "approval_required": True,
                "priority": "high",
            }
        )
    actions.append(
        {
            "title": "Review correlated evidence and preserve logs",
            "impact": "Protects forensic context before any disruptive response is applied.",
            "approval_required": True,
            "priority": "medium",
        }
    )
    actions.append(
        {
            "title": "Increase monitoring on related identities and assets",
            "impact": "Helps detect spread or follow-on actions with minimal disruption.",
            "approval_required": True,
            "priority": "medium",
        }
    )
    return actions[:4]


def _build_business_impact(evidence_package: dict[str, Any]) -> list[str]:
    entities = evidence_package.get("entities", {})
    impacts = []
    if entities.get("users"):
        impacts.append("Potential unauthorized account activity affecting business users.")
    if entities.get("hosts"):
        impacts.append("Operational disruption risk to impacted hosts or connected systems.")
    if any("Send" in str(action) or "Mail" in str(action) for action in entities.get("actions", [])):
        impacts.append("Potential exposure of internal communications or customer-facing correspondence.")
    if any("FILE_WRITE" in str(action) or "VSS_DELETE" in str(action) for action in entities.get("actions", [])):
        impacts.append("Potential data integrity or recovery impact if destructive actions continue.")
    if not impacts:
        impacts.append("Potential business disruption if the suspicious pattern is not contained.")
    return impacts[:3]


def _build_grounded_playbook(evidence_package: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    priority = evidence_package.get("priority", {})
    summary = evidence_package.get("summary", {})
    entities = evidence_package.get("entities", {})
    evidence_panel = _build_evidence_panel(evidence_package)
    risk_breakdown = _build_risk_breakdown(evidence_package, evidence_panel)
    weighted_score = int(round(min(100.0, max(0.0, float(priority.get("score", 0.0)) * 100 + sum(item["risk_contribution"] for item in evidence_panel[:2]) * 0.4))))
    confidence_score = int(round(min(100.0, max(0.0, float(priority.get("confidence", 0.0)) * 100))))
    user_label = entities.get("users", ["user"])[0]
    event_kind = ", ".join(summary.get("event_kinds", [])) or "security"

    incident_summary = (
        f"Suspicious {event_kind} activity detected for {user_label} "
        f"with correlated actions suggesting possible account misuse."
    )
    confidence_reasons = list(priority.get("reasons", [])) or ["Correlated incident evidence supports analyst review."]
    rationale = " ; ".join(confidence_reasons[:3])
    explainability = (
        "TrustSphere flagged this incident because multiple abnormal signals were observed in the same "
        f"incident window and correlated into a single evidence-backed case. {rationale}."
    )
    if reason:
        explainability += f" Playbook content was generated deterministically because the LLM path returned: {reason}."

    return {
        "incident_summary": incident_summary,
        "evidence_panel": evidence_panel,
        "risk_score": {"score": weighted_score, "label": _risk_label(weighted_score)},
        "risk_breakdown": risk_breakdown,
        "confidence_level": {"level": _confidence_level(confidence_score), "score": confidence_score},
        "confidence_rationale": confidence_reasons,
        "attack_stage": _attack_stage(evidence_package),
        "recommended_actions": _build_recommended_actions(evidence_package),
        "approval_requirement": "Requires analyst approval within 60 seconds.",
        "business_impact": _build_business_impact(evidence_package),
        "explainability": explainability,
        "audience": "analyst_only",
        "approval_mode": "human_approval_required",
        "playbook_status": "grounded_fallback",
    }


def _fallback_playbook(evidence_package: dict[str, Any], reason: str) -> dict[str, Any]:
    return _build_grounded_playbook(evidence_package, reason)


def _normalize_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key, [])
    return value if isinstance(value, list) else []


def _playbook_has_required_structure(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    for key in PLAYBOOK_SCHEMA["required_keys"]:
        if key not in payload:
            return False
    return True


def _validate_playbook_payload(payload: dict[str, Any]) -> dict[str, Any]:
    grounded = _build_grounded_playbook(
        {
            "priority": {"score": 0.0, "confidence": 0.0, "reasons": []},
            "summary": {},
            "entities": {},
            "timeline": [],
            "structured_evidence": [],
        }
    )
    payload = {
        **grounded,
        **payload,
    }
    for key in PLAYBOOK_SCHEMA["required_keys"]:
        payload.setdefault(key, grounded.get(key, [] if key.endswith("s") else ""))
    actions = _normalize_list(payload, "recommended_actions")
    normalized_actions = []
    for action in actions:
        normalized = {field: action.get(field) for field in PLAYBOOK_SCHEMA["required_action_keys"]}
        normalized["approval_required"] = True
        normalized_actions.append(normalized)
    payload["recommended_actions"] = normalized_actions
    evidence_entries = _normalize_list(payload, "evidence_panel")
    payload["evidence_panel"] = [
        {field: entry.get(field) for field in PLAYBOOK_SCHEMA["required_evidence_keys"]}
        for entry in evidence_entries
    ]
    breakdown_entries = _normalize_list(payload, "risk_breakdown")
    payload["risk_breakdown"] = [
        {field: entry.get(field) for field in PLAYBOOK_SCHEMA["required_risk_breakdown_keys"]}
        for entry in breakdown_entries
    ]
    payload["audience"] = "analyst_only"
    payload["approval_mode"] = "human_approval_required"
    return payload


def generate_playbook_for_incident(priority_record: dict[str, Any], provider: str | None = None) -> dict[str, Any]:
    evidence_package = serialize_incident_for_llm(priority_record)
    client = build_llm_client(provider=provider)
    response = client.generate(build_playbook_messages(evidence_package))
    if response.status != "ok" or not _playbook_has_required_structure(response.parsed_json):
        fallback_reason = "ollama_response_invalid_or_unavailable"
        playbook = _fallback_playbook(evidence_package, fallback_reason)
        llm_status = "fallback"
    else:
        playbook = _validate_playbook_payload(response.parsed_json)
        llm_status = "ok"
    return {
        "incident_id": priority_record["incident_id"],
        "provider": response.provider,
        "llm_status": llm_status,
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
