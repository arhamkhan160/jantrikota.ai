"""
tests/test_auth.py
Real JWT enforcement — clears the conftest auth bypass and verifies tokens the
way Supabase-signed ones are verified (HS256 with the project secret).
"""

import time

import jwt
from fastapi.testclient import TestClient

from main import app
from core.config import settings

SECRET = "test-secret-123"


def _token(**override) -> str:
    payload = {"sub": "u1", "aud": "authenticated", "email": "a@b.co",
               "exp": int(time.time()) + 3600}
    payload.update(override)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def _client(monkeypatch) -> TestClient:
    app.dependency_overrides.clear()                       # exercise the real dependency
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", SECRET)
    return TestClient(app)


def test_protected_route_requires_token(monkeypatch):
    c = _client(monkeypatch)
    assert c.get("/api/v1/auth/me").status_code == 401


def test_valid_token_accepted(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 200 and r.json()["email"] == "a@b.co"


def test_bad_token_rejected(monkeypatch):
    c = _client(monkeypatch)
    assert c.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_expired_token_rejected(monkeypatch):
    c = _client(monkeypatch)
    tok = _token(exp=int(time.time()) - 10)
    assert c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_functional_route_locked_without_token(monkeypatch):
    c = _client(monkeypatch)
    # a real pipeline route must be unreachable without a token (auth runs first)
    assert c.get("/api/v1/pipeline/status/anything").status_code == 401


def test_wrong_secret_rejected(monkeypatch):
    c = _client(monkeypatch)
    forged = jwt.encode({"sub": "u", "aud": "authenticated", "exp": int(time.time()) + 60},
                        "attacker-secret", algorithm="HS256")
    assert c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
