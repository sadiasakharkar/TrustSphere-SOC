from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    email: str
    role: str
    created_at: datetime
    expires_at: datetime
    invalidated_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.invalidated_at is None and self.expires_at > utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "active": self.active,
        }


@dataclass(slots=True)
class UploadRecord:
    upload_id: str
    filename: str
    stored_path: str
    sha256: str
    size_bytes: int
    content_type: str | None
    dataset_id: str
    domain: str
    uploaded_by: str
    uploaded_at: datetime
    status: str = "uploaded"
    processing_notes: list[str] = field(default_factory=list)
    normalized_events: list[dict[str, Any]] = field(default_factory=list)
    suspicious_events: list[dict[str, Any]] = field(default_factory=list)
    incidents: list[dict[str, Any]] = field(default_factory=list)
    priority_records: list[dict[str, Any]] = field(default_factory=list)
    playbooks: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "dataset_id": self.dataset_id,
            "domain": self.domain,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat(),
            "status": self.status,
            "processing_notes": self.processing_notes,
            "normalized_event_count": len(self.normalized_events),
            "suspicious_event_count": len(self.suspicious_events),
            "incident_count": len(self.incidents),
        }


class InMemoryStore:
    def __init__(self, session_ttl_minutes: int) -> None:
        self._lock = RLock()
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self.sessions: dict[str, SessionRecord] = {}
        self.revoked_sessions: set[str] = set()
        self.uploads: dict[str, UploadRecord] = {}
        self.latest_upload_id: str | None = None

    def create_session(self, session_id: str, email: str, role: str = "analyst") -> SessionRecord:
        with self._lock:
            now = utc_now()
            record = SessionRecord(
                session_id=session_id,
                email=email,
                role=role,
                created_at=now,
                expires_at=now + self.session_ttl,
            )
            self.sessions[session_id] = record
            self.revoked_sessions.discard(session_id)
            return record

    def get_session(self, session_id: str | None) -> SessionRecord | None:
        if not session_id:
            return None
        with self._lock:
            record = self.sessions.get(session_id)
            if record is None:
                return None
            if session_id in self.revoked_sessions or not record.active:
                return None
            return record

    def revoke_session(self, session_id: str | None) -> None:
        if not session_id:
            return
        with self._lock:
            record = self.sessions.get(session_id)
            if record is not None:
                record.invalidated_at = utc_now()
            self.revoked_sessions.add(session_id)

    def put_upload(self, record: UploadRecord) -> None:
        with self._lock:
            self.uploads[record.upload_id] = record
            self.latest_upload_id = record.upload_id

    def get_upload(self, upload_id: str) -> UploadRecord | None:
        with self._lock:
            return self.uploads.get(upload_id)

    def list_uploads(self) -> list[UploadRecord]:
        with self._lock:
            return sorted(self.uploads.values(), key=lambda item: item.uploaded_at, reverse=True)
