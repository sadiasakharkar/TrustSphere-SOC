from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from backend.config import settings
from backend.models import (
    AnalystDecisionRequest,
    LoginRequest,
    LoginResponse,
    MonitoringSummaryResponse,
    NormalizeResponse,
    UploadResponse,
)
from backend.security import clear_session_cookie, issue_session, require_session, set_session_cookie
from backend.services import (
    build_explanation,
    build_monitoring_summary,
    generate_incident_records,
    infer_dataset_id,
    normalize_upload,
    persist_upload,
    playbook_for_record,
    save_analyst_feedback,
)
from backend.state import InMemoryStore, SessionRecord


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Secure, explainable backend for TrustSphere SOC. "
        "This MVP uses in-memory session state and local file storage instead of a database."
    ),
)

if settings.enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.state.store = InMemoryStore(settings.session_ttl_minutes)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if settings.enforce_https and request.headers.get("x-forwarded-proto", request.url.scheme) != "https":
        return Response(
            content='{"detail":"HTTPS is required for this deployment."}',
            media_type="application/json",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    if settings.enforce_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def _find_upload_or_404(upload_id: str):
    record = app.state.store.get_upload(upload_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} was not found.")
    return record


def _find_priority_record_or_404(incident_id: str):
    for upload in app.state.store.list_uploads():
        for priority_record in upload.priority_records:
            if priority_record["incident_id"] == incident_id:
                return upload, priority_record
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} was not found.")


@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "message": "TrustSphere backend is running.",
    }


@app.get("/favicon.ico", status_code=204)
def favicon() -> Response:
    return Response(status_code=204)


@app.post("/analyze")
async def analyze(request: Request) -> dict[str, Any]:
    payload = await request.json()
    text_parts: list[str] = []
    if isinstance(payload, dict):
        for key in ("content", "text", "pageContent", "body", "html", "url", "title"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
    combined_text = "\n".join(text_parts).strip()
    snippet = combined_text[:400]

    indicators = {
        "contains_login": "login" in combined_text.lower(),
        "contains_password": "password" in combined_text.lower(),
        "contains_bank_terms": any(term in combined_text.lower() for term in ("bank", "account", "transfer", "payment")),
        "length": len(combined_text),
    }

    return {
        "status": "ok",
        "message": "TrustSphere analyze endpoint is available.",
        "summary": {
            "received_fields": sorted(payload.keys()) if isinstance(payload, dict) else [],
            "text_excerpt": snippet,
            "indicator_summary": indicators,
        },
    }


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response):
    if not settings.demo_auth_mode:
        raise HTTPException(status_code=503, detail="Demo auth mode is disabled and no identity provider is configured.")
    session = issue_session(app.state.store, email=payload.email)
    set_session_cookie(response, session.session_id)
    return {
        "message": "Login successful. Demo mode accepts any non-empty credentials and still enforces server-side logout invalidation.",
        "user": {
            "email": payload.email,
            "role": session.role,
            "session_expires_at": session.expires_at.isoformat(),
            "auth_mode": "demo",
        },
    }


@app.post("/api/auth/logout")
def logout(response: Response, session: SessionRecord = Depends(require_session)):
    app.state.store.revoke_session(session.session_id)
    clear_session_cookie(response)
    return {
        "message": "Logout successful.",
        "security": {
            "server_side_session_invalidated": True,
            "cookies_cleared": True,
        },
    }


@app.get("/api/auth/me")
def me(session: SessionRecord = Depends(require_session)):
    return {
        "email": session.email,
        "role": session.role,
        "created_at": session.created_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
    }


@app.post("/api/uploads/logs", response_model=UploadResponse)
async def upload_logs(
    file: UploadFile = File(...),
    dataset_id: str | None = Form(default=None),
    domain: str = Form(default=settings.default_domain),
    session: SessionRecord = Depends(require_session),
):
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail="Only .json and .csv files are accepted.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")

    record = persist_upload(
        filename=filename,
        content=content,
        content_type=file.content_type,
        uploaded_by=session.email,
        dataset_id=infer_dataset_id(filename, override=dataset_id),
        domain=domain,
    )
    app.state.store.put_upload(record)
    return {
        "upload_id": record.upload_id,
        "status": record.status,
        "filename": record.filename,
        "dataset_id": record.dataset_id,
        "domain": record.domain,
        "sha256": record.sha256,
        "size_bytes": record.size_bytes,
    }


@app.get("/api/uploads")
def list_uploads(session: SessionRecord = Depends(require_session)):
    return {"items": [record.to_summary() for record in app.state.store.list_uploads()], "requested_by": session.email}


@app.get("/api/uploads/{upload_id}/status")
def upload_status(upload_id: str, session: SessionRecord = Depends(require_session)):
    record = _find_upload_or_404(upload_id)
    return record.to_summary()


@app.post("/api/normalize/{upload_id}", response_model=NormalizeResponse)
def normalize(upload_id: str, session: SessionRecord = Depends(require_session)):
    record = _find_upload_or_404(upload_id)
    try:
        return normalize_upload(record)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Normalization failed: {exc}") from exc


@app.get("/api/normalize/{upload_id}/results")
def normalize_results(upload_id: str, session: SessionRecord = Depends(require_session)):
    record = _find_upload_or_404(upload_id)
    if not record.normalized_events:
        raise HTTPException(status_code=409, detail="Normalization has not run for this upload yet.")
    return {
        "upload": record.to_summary(),
        "events": record.normalized_events,
        "suspicious_events": record.suspicious_events,
    }


@app.post("/api/incidents/generate/{upload_id}")
def generate_incidents(upload_id: str, session: SessionRecord = Depends(require_session)):
    record = _find_upload_or_404(upload_id)
    try:
        return generate_incident_records(record)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Incident generation failed: {exc}") from exc


@app.get("/api/incidents")
def incidents(session: SessionRecord = Depends(require_session)):
    items = []
    for upload in app.state.store.list_uploads():
        for priority_record in upload.priority_records:
            items.append(
                {
                    "upload_id": upload.upload_id,
                    "incident_id": priority_record["incident_id"],
                    "priority_label": priority_record["priority_label"],
                    "priority_score": priority_record["priority_score"],
                    "reasons": priority_record["reasons"],
                    "incident": priority_record["incident"],
                }
            )
    items.sort(key=lambda item: item["priority_score"], reverse=True)
    return {"items": items}


@app.get("/api/incidents/{incident_id}")
def incident_detail(incident_id: str, session: SessionRecord = Depends(require_session)):
    upload, priority_record = _find_priority_record_or_404(incident_id)
    return {
        "upload_id": upload.upload_id,
        "priority": {
            "incident_id": priority_record["incident_id"],
            "priority_label": priority_record["priority_label"],
            "priority_score": priority_record["priority_score"],
            "reasons": priority_record["reasons"],
            "score_breakdown": priority_record["score_breakdown"],
        },
        "incident": priority_record["incident"],
    }


@app.get("/api/incidents/{incident_id}/explanation")
def incident_explanation(incident_id: str, session: SessionRecord = Depends(require_session)):
    _, priority_record = _find_priority_record_or_404(incident_id)
    return build_explanation(priority_record)


@app.get("/api/incidents/{incident_id}/terminal")
def incident_terminal(incident_id: str, session: SessionRecord = Depends(require_session)):
    _, priority_record = _find_priority_record_or_404(incident_id)
    return {
        "incident_id": incident_id,
        "triage": {
            "priority_label": priority_record["priority_label"],
            "priority_score": priority_record["priority_score"],
            "reasons": priority_record["reasons"],
        },
        "incident": priority_record["incident"],
        "explanation": build_explanation(priority_record),
    }


@app.get("/api/incidents/{incident_id}/playbook")
def incident_playbook(incident_id: str, session: SessionRecord = Depends(require_session)):
    upload, _ = _find_priority_record_or_404(incident_id)
    try:
        return playbook_for_record(upload, incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Playbook target {incident_id} was not found.") from exc


@app.post("/api/incidents/{incident_id}/feedback")
def incident_feedback(
    incident_id: str,
    payload: AnalystDecisionRequest,
    session: SessionRecord = Depends(require_session),
):
    if payload.incident_id != incident_id:
        raise HTTPException(status_code=400, detail="Incident ID in payload does not match route.")
    _, priority_record = _find_priority_record_or_404(incident_id)
    feedback = save_analyst_feedback(priority_record, verdict=payload.verdict, notes=payload.notes)
    feedback["submitted_by"] = session.email
    return feedback


@app.get("/api/monitoring/summary", response_model=MonitoringSummaryResponse)
def monitoring_summary(session: SessionRecord = Depends(require_session)):
    latest = None
    if app.state.store.latest_upload_id:
        latest = app.state.store.get_upload(app.state.store.latest_upload_id)
    return build_monitoring_summary(latest)
