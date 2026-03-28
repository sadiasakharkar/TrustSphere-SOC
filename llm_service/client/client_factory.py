from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_service.client.ollama_client import OllamaClient
from llm_service.client.remote_secure_client import RemoteSecureLLMClient


def load_llm_config(path: str | Path = Path("configs/llm_config.json")) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_llm_client(provider: str | None = None, config_path: str | Path = Path("configs/llm_config.json")):
    config = load_llm_config(config_path)
    provider = provider or config.get("default_provider", "ollama")
    if provider == "ollama":
        ollama = config["ollama"]
        return OllamaClient(
            base_url=ollama["base_url"],
            model=ollama["model"],
            timeout_seconds=int(ollama.get("timeout_seconds", 90)),
        )
    if provider == "remote":
        remote = config["remote"]
        return RemoteSecureLLMClient(
            base_url=remote["base_url"],
            generate_path=remote["generate_path"],
            auth_header=remote["auth_header"],
            api_key_env=remote["api_key_env"],
            request_signing_secret_env=remote.get("request_signing_secret_env"),
            timeout_seconds=int(remote.get("timeout_seconds", 90)),
            verify_tls=bool(remote.get("verify_tls", True)),
        )
    raise ValueError(f"Unsupported provider: {provider}")
