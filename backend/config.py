from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    app_name: str = "TrustSphere SOC API"
    environment: str = os.getenv("TRUSTSPHERE_ENV", "development")
    frontend_origins: list[str] = None  # type: ignore[assignment]
    runtime_dir: Path = Path(os.getenv("TRUSTSPHERE_RUNTIME_DIR", "runtime"))
    cookie_name: str = os.getenv("TRUSTSPHERE_COOKIE_NAME", "trustsphere_session")
    session_ttl_minutes: int = int(os.getenv("TRUSTSPHERE_SESSION_TTL_MINUTES", "720"))
    max_upload_size_bytes: int = int(os.getenv("TRUSTSPHERE_MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
    enforce_https: bool = _as_bool(os.getenv("TRUSTSPHERE_ENFORCE_HTTPS"), False)
    secure_cookies: bool = _as_bool(os.getenv("TRUSTSPHERE_SECURE_COOKIES"), False)
    same_site: str = os.getenv("TRUSTSPHERE_COOKIE_SAMESITE", "lax")
    default_domain: str = os.getenv("TRUSTSPHERE_DEFAULT_DOMAIN", "network_security")
    default_csv_dataset_id: str = os.getenv("TRUSTSPHERE_DEFAULT_CSV_DATASET_ID", "cyber_threat_logs_v1")
    default_json_dataset_id: str = os.getenv("TRUSTSPHERE_DEFAULT_JSON_DATASET_ID", "json_demo")
    allowed_extensions: tuple[str, ...] = (".csv", ".json")
    demo_auth_mode: bool = _as_bool(os.getenv("TRUSTSPHERE_DEMO_AUTH_MODE"), True)
    llm_provider: str | None = os.getenv("TRUSTSPHERE_LLM_PROVIDER")

    def __post_init__(self) -> None:
        self.frontend_origins = _split_csv(
            os.getenv(
                "TRUSTSPHERE_FRONTEND_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        )
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        (self.runtime_dir / "uploads").mkdir(parents=True, exist_ok=True)

    @property
    def uploads_dir(self) -> Path:
        return self.runtime_dir / "uploads"


settings = Settings()
