from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_service.client.client_factory import load_llm_config


def main() -> None:
    config = load_llm_config()
    ollama = config["ollama"]
    base_url = ollama["base_url"].rstrip("/")
    model = ollama["model"]
    result = {
        "provider": "ollama",
        "enforce_ollama_only": bool(config.get("enforce_ollama_only", False)),
        "base_url": base_url,
        "model": model,
        "reachable": False,
        "model_available": False,
    }

    try:
        with urlopen(f"{base_url}/api/tags", timeout=int(ollama.get("timeout_seconds", 90))) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result["reachable"] = True
            models = [item.get("name") for item in payload.get("models", [])]
            result["available_models"] = models
            result["model_available"] = model in models
    except (HTTPError, URLError, TimeoutError) as exc:
        result["error"] = str(exc)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
