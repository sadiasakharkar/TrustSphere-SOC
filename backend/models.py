from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthUser(BaseModel):
    email: str
    role: str
    session_expires_at: str
    auth_mode: str


class LoginResponse(BaseModel):
    message: str
    user: AuthUser


class UploadResponse(BaseModel):
    upload_id: str
    status: str
    filename: str
    dataset_id: str
    domain: str
    sha256: str
    size_bytes: int


class UploadStatusResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    upload_id: str
    status: str


class NormalizeResponse(BaseModel):
    upload_id: str
    status: str
    normalized_event_count: int
    suspicious_event_count: int
    label_counts: dict[str, int]
    severity_counts: dict[str, int]


class IncidentGenerationResponse(BaseModel):
    upload_id: str
    status: str
    incident_count: int
    top_incident_id: str | None


class MonitoringSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    upload_id: str | None
    status: str


class AnalystDecisionRequest(BaseModel):
    incident_id: str
    verdict: str = Field(pattern="^(true_positive|false_positive|needs_review)$")
    notes: str | None = Field(default=None, max_length=1000)
