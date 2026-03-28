from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from llm_service.client.ollama_client import LLMResponse
from llm_service.secure_channel.request_signer import build_signed_headers


class RemoteSecureLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        generate_path: str,
        auth_header: str,
        api_key_env: str,
        request_signing_secret_env: str | None = None,
        timeout_seconds: int = 90,
        verify_tls: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.generate_path = generate_path
        self.auth_header = auth_header
        self.api_key_env = api_key_env
        self.request_signing_secret_env = request_signing_secret_env
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls

    def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        payload = {"messages": messages}
        body_text = json.dumps(payload)
        headers = build_signed_headers(
            body=body_text,
            api_key_env=self.api_key_env,
            auth_header=self.auth_header,
            signing_secret_env=self.request_signing_secret_env,
        )
        request = Request(
            f"{self.base_url}{self.generate_path}",
            data=body_text.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        ssl_context = ssl.create_default_context()
        if not self.verify_tls:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        try:
            with urlopen(request, timeout=self.timeout_seconds, context=ssl_context) as response:
                parsed = json.loads(response.read().decode("utf-8"))
                raw_text = parsed.get("content", "")
                return LLMResponse(
                    provider="remote-secure",
                    raw_text=raw_text,
                    parsed_json=_try_parse_json(raw_text),
                    status="ok",
                )
        except (HTTPError, URLError, TimeoutError) as exc:
            return LLMResponse(
                provider="remote-secure",
                raw_text=str(exc),
                parsed_json=None,
                status="error",
            )


def _try_parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
