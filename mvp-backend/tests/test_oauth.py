"""
Tests for the Google OAuth flow (app/oauth/*): signed-state round-trip and the
authorize-url / callback / status / disconnect endpoints via TestClient, with the
live Google calls mocked. Hermetic — temp DuckDB, no network.
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

os.environ["MVP_DUCKDB_PATH"] = str(Path(tempfile.mkdtemp()) / "oauth.duckdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

from app.oauth import google_flow, state as oauth_state  # noqa: E402
from app.oauth.google_flow import ExchangeResult  # noqa: E402
import app.server as server  # noqa: E402


# ── state signing ────────────────────────────────────────────────────────────

def test_state_sign_verify_and_tamper():
    token = oauth_state.sign_state({"user_id": "u1", "kinds": ["email"]})
    assert oauth_state.verify_state(token) == {"user_id": "u1", "kinds": ["email"]}
    with pytest.raises(ValueError):
        oauth_state.verify_state(token + "x")
    with pytest.raises(ValueError):
        oauth_state.verify_state("garbage")


# ── HTTP endpoints ───────────────────────────────────────────────────────────

def _reconnect_shared_storage():
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _token(client, user_id: str) -> str:
    r = client.post("/auth/issue-token", json={"user_id": user_id})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_oauth_endpoints_end_to_end(monkeypatch):
    # Mock the live Google calls.
    monkeypatch.setattr(google_flow, "is_configured", lambda: True)
    monkeypatch.setattr(
        google_flow, "build_authorization_url",
        lambda **kw: f"https://accounts.google.com/o/oauth2/auth?state={kw['state']}",
    )
    monkeypatch.setattr(
        google_flow, "exchange_code",
        lambda **kw: ExchangeResult(
            refresh_token="1//refresh-xyz", scopes=kw["scopes"], email="parent@example.com"
        ),
    )

    try:
        with TestClient(server.app) as client:
            uid = "oauth-test-user"
            auth = {"Authorization": f"Bearer {_token(client, uid)}"}

            # authorize-url requires auth
            assert client.get("/oauth/google/authorize-url").status_code == 401

            # authorize-url returns a Google consent URL + a verifiable state
            r = client.get("/oauth/google/authorize-url?kinds=email,calendar", headers=auth)
            assert r.status_code == 200, r.text
            url = r.json()["authorization_url"]
            assert "accounts.google.com" in url
            state = url.split("state=")[1]
            decoded = oauth_state.verify_state(state)
            assert decoded["user_id"] == uid
            assert decoded["kinds"] == ["email", "calendar"]
            assert decoded["cv"]  # PKCE verifier carried in the state

            # invalid kinds → 400
            assert client.get("/oauth/google/authorize-url?kinds=foo", headers=auth).status_code == 400

            # callback success: stores one row per kind, redirects to app scheme
            r = client.get(
                f"/oauth/google/callback?code=abc&state={state}", follow_redirects=False
            )
            assert r.status_code in (302, 307)
            assert r.headers["location"].startswith("mvparent://oauth/google?status=success")

            # status lists both connected kinds, never the token
            r = client.get("/oauth/google/status", headers=auth)
            assert r.status_code == 200
            body = r.json()
            kinds = sorted(a["kind"] for a in body["accounts"])
            assert kinds == ["calendar", "email"]
            assert all(a["account_email"] == "parent@example.com" for a in body["accounts"])
            assert "encrypted_refresh_token" not in str(body)

            # disconnect one kind
            r = client.post(
                "/oauth/google/disconnect", json={"user_id": uid, "kind": "email"}, headers=auth
            )
            assert r.status_code == 200
            r = client.get("/oauth/google/status", headers=auth)
            connected = [a for a in r.json()["accounts"] if a["status"] == "connected"]
            assert sorted(a["kind"] for a in connected) == ["calendar"]

            # ── callback failure paths ────────────────────────────────
            r = client.get("/oauth/google/callback?error=access_denied", follow_redirects=False)
            assert r.headers["location"].startswith("mvparent://oauth/google?status=error")
            r = client.get("/oauth/google/callback?code=x&state=bad", follow_redirects=False)
            assert "status=error" in r.headers["location"]
            assert "bad_state" in r.headers["location"]

            # no refresh token → error redirect (no row written)
            monkeypatch.setattr(
                google_flow, "exchange_code",
                lambda **kw: ExchangeResult(refresh_token=None, scopes=[], email=None),
            )
            good_state = oauth_state.sign_state(
                {"user_id": uid, "kinds": ["calendar"], "cv": "test-verifier"}
            )
            r = client.get(
                f"/oauth/google/callback?code=abc&state={good_state}", follow_redirects=False
            )
            assert "no_refresh_token" in r.headers["location"]
    finally:
        _reconnect_shared_storage()


def test_authorize_url_503_when_unconfigured(monkeypatch):
    monkeypatch.setattr(google_flow, "is_configured", lambda: False)
    try:
        with TestClient(server.app) as client:
            auth = {"Authorization": f"Bearer {_token(client, 'u2')}"}
            r = client.get("/oauth/google/authorize-url", headers=auth)
            assert r.status_code == 503
    finally:
        _reconnect_shared_storage()
