from __future__ import annotations


PRIMARY_LABEL_MAP = {
    "benign": "false_positive",
    "suspicious": "uncertain",
    "malicious": "true_positive",
}

EMAIL_LABEL_MAP = {
    "0": "false_positive",
    "1": "true_positive",
}

WEBSITE_LABEL_MAP = {
    "-1": "false_positive",
    "0": "uncertain",
    "1": "true_positive",
}


def map_dataset_label(dataset_id: str, raw_label: str | None) -> str | None:
    if raw_label in (None, ""):
        return None
    if dataset_id == "cyber_threat_logs_v1":
        return PRIMARY_LABEL_MAP.get(str(raw_label).strip().lower())
    if dataset_id in {"email_text_v1", "nazario_email_url_v1"}:
        return EMAIL_LABEL_MAP.get(str(raw_label).strip())
    if dataset_id in {"website_phishing_v1", "phishing_arff_v1"}:
        return WEBSITE_LABEL_MAP.get(str(raw_label).strip())
    return None
