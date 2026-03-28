from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(slots=True)
class LLMResponse:
    provider: str
    raw_text: str
    parsed_json: dict[str, Any] | None
    status: str


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 90,
        keep_alive: str | None = None,
        num_predict: int = 512,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.keep_alive = keep_alive
        self.num_predict = num_predict

    def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": self.num_predict,
            },
        }
        if self.keep_alive:
            payload["keep_alive"] = self.keep_alive
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                parsed = json.loads(response.read().decode("utf-8"))
                raw_text = parsed.get("message", {}).get("content", "")
                return LLMResponse(
                    provider="ollama",
                    raw_text=raw_text,
                    parsed_json=_try_parse_json(raw_text),
                    status="ok",
                )
        except (HTTPError, URLError, TimeoutError) as exc:
            return LLMResponse(
                provider="ollama",
                raw_text=str(exc),
                parsed_json=None,
                status="error",
            )


def _try_parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced_start = text.find("```json")
    if fenced_start != -1:
        fenced_start = text.find("\n", fenced_start)
        fenced_end = text.find("```", fenced_start + 1)
        if fenced_start != -1 and fenced_end != -1:
            candidate = text[fenced_start + 1:fenced_end].strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None
