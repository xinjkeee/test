from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_input_has_readable_error() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/generate", json={"name": " "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
