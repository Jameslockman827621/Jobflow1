"""Lightweight smoke tests — no database required."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert data.get("docs") == "/docs"


def test_health():
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
