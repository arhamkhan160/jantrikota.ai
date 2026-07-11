"""
tests/test_health.py
Basic smoke tests for health and root endpoints.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200
