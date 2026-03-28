from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any


def build_signed_headers(
    *,
    body: str,
    api_key_env: str,
    auth_header: str,
    signing_secret_env: str | None = None,
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    api_key = os.environ.get(api_key_env)
    if api_key:
        headers[auth_header] = api_key

    if signing_secret_env:
        secret = os.environ.get(signing_secret_env)
        if secret:
            signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
            headers["X-TrustSphere-Signature"] = signature
    return headers
