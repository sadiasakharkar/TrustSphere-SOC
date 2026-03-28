from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "analyst@trustsphere.local", "password": "demo-password"},
    )
    assert response.status_code == 200


def test_backend_api_end_to_end() -> None:
    app.state.store.sessions.clear()
    app.state.store.revoked_sessions.clear()
    app.state.store.uploads.clear()
    app.state.store.latest_upload_id = None

    client = TestClient(app)
    _login(client)

    fixture = Path("tests/fixtures/correlation_events.json")
    with fixture.open("rb") as handle:
        response = client.post(
            "/api/uploads/logs",
            files={"file": ("correlation_events.json", handle, "application/json")},
        )
    assert response.status_code == 200
    upload_id = response.json()["upload_id"]

    response = client.post(f"/api/normalize/{upload_id}")
    assert response.status_code == 200
    assert response.json()["normalized_event_count"] > 0

    response = client.post(f"/api/incidents/generate/{upload_id}")
    assert response.status_code == 200

    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()["items"]
    assert incidents

    incident_id = incidents[0]["incident_id"]

    response = client.get(f"/api/incidents/{incident_id}/explanation")
    assert response.status_code == 200
    explanation = response.json()
    assert explanation["incident_id"] == incident_id
    assert "what" in explanation

    response = client.post("/api/auth/logout")
    assert response.status_code == 200

    response = client.get("/api/auth/me")
    assert response.status_code == 401
