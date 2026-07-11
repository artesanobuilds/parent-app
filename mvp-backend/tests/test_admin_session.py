"""CMS admin auth (app/admin_auth.py): header path, cookie-session path, CSRF
marker, token-rotation invalidation. The CMS SPA no longer ships ADMIN_TOKEN
in its bundle — it logs in via POST /admin/session.

One TestClient context for the whole module: its lifespan-exit closes the
shared storage singleton, so we enter it once and rebuild storage afterwards
(same pattern as tests/test_cos_api.py).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "admin_session.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402

ADMIN = "test-admin-token-123"
# An admin-gated endpoint with no side effects.
PROBE = "/cms/stats"


@pytest.fixture(scope="module")
def client():
    # https base URL: the session cookie is Secure, and the cookie jar won't
    # send Secure cookies over plain http (prod is HTTPS at Railway anyway).
    # Rebuild the shared storage singleton before + after our lifespan so
    # cross-module ordering (a prior module closed it) can't poison us.
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app, base_url="https://testserver") as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture(autouse=True)
def _fresh_session(client):
    client.cookies.clear()
    yield


def test_admin_endpoints_fail_closed_without_admin_token_env(client, monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    assert client.get(PROBE).status_code == 503
    assert client.post("/admin/session", json={"token": "x"}).status_code == 503


def test_header_auth_still_works_for_scripts(client, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    assert client.get(PROBE).status_code == 401
    assert client.get(PROBE, headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.get(PROBE, headers={"X-Admin-Token": ADMIN}).status_code == 200


def test_cookie_session_login_and_use(client, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    # Wrong token → 401, no cookie.
    bad = client.post("/admin/session", json={"token": "wrong"})
    assert bad.status_code == 401
    assert "admin_session" not in client.cookies

    ok = client.post("/admin/session", json={"token": ADMIN})
    assert ok.status_code == 200
    assert "admin_session" in client.cookies

    # Cookie alone is NOT enough — the CSRF marker is required.
    assert client.get(PROBE).status_code == 401
    # Cookie + X-Requested-With: cms → authorized.
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 200


def test_rotating_admin_token_kills_outstanding_sessions(client, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    assert client.post("/admin/session", json={"token": ADMIN}).status_code == 200
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 200
    # Rotate the operator secret → the session payload's fingerprint no
    # longer matches → every outstanding cookie is dead.
    monkeypatch.setenv("ADMIN_TOKEN", "rotated-token-456")
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 401


def test_logout_clears_cookie(client, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    client.post("/admin/session", json={"token": ADMIN})
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 200
    client.delete("/admin/session")
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 401


def test_forged_cookie_rejected(client, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    client.cookies.set("admin_session", "gAAAAABforged-not-a-fernet-token")
    assert client.get(PROBE, headers={"X-Requested-With": "cms"}).status_code == 401
