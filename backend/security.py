from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, Response, status

from backend.config import settings
from backend.state import InMemoryStore, SessionRecord


UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required.",
)


def issue_session(store: InMemoryStore, email: str, role: str = "analyst") -> SessionRecord:
    return store.create_session(secrets.token_urlsafe(32), email=email, role=role)


def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.same_site,
        max_age=settings.session_ttl_minutes * 60,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.same_site,
    )


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


def require_session(
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> SessionRecord:
    session_id = request.cookies.get(settings.cookie_name)
    session = store.get_session(session_id)
    if session is None:
        raise UNAUTHORIZED
    return session
