"""Google web-redirect login (one-time code) + dashboard pairing code.

The Google code exchange + JWKS verification are monkeypatched (no network),
mirroring tests/test_oauth.py's mocking of the Google flow.
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

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "auth_google.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret-google")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
import app.auth_login_google as login_google  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


# ── One-time login code (the piece the Google redirect hands back) ───────────

def test_login_code_single_use_and_expiry(client):
    from app.duckdb_storage import DuckDBStorage
    # The code carries a VERIFIED identity; the exchange resolves/creates the
    # account (identity binding is deferred from the redirect to here).
    code = login_google.mint_login_code(
        provider="google", provider_sub="gsub-code-1",
        email="c@example.com", email_verified=True,
    )

    # First exchange works: creates an account bound to the google sub.
    r1 = client.post("/auth/exchange-code", json={"login_code": code, "platform": "web"})
    assert r1.status_code == 200, r1.text
    assert r1.json()["access_token"].count(".") == 2
    assert r1.json()["is_new_account"] is True
    user_id = r1.json()["user_id"]
    assert server.storage_backend.get_identity("google", "gsub-code-1")["user_id"] == user_id

    # Reusing the same code fails (single use).
    r2 = client.post("/auth/exchange-code", json={"login_code": code})
    assert r2.status_code == 401


def test_exchange_code_claims_legacy_account(client):
    # A legacy user exists; a Google login through the redirect must CLAIM it
    # (bind the google identity to the existing user_id), not create a fresh one.
    legacy = client.post("/auth/issue-token", json={"user_id": "google-legacy-user"}).json()["token"]
    code = login_google.mint_login_code(
        provider="google", provider_sub="gsub-legacy-1",
        email="gl@example.com", email_verified=True,
    )
    res = client.post("/auth/exchange-code", json={
        "login_code": code, "platform": "ios",
        "legacy_user_id": "google-legacy-user", "legacy_token": legacy,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["user_id"] == "google-legacy-user"   # claimed, same account
    assert body["linked_legacy"] is True
    assert body["is_new_account"] is False


def test_exchange_rejects_garbage_code(client):
    assert client.post("/auth/exchange-code", json={"login_code": "not-a-real-code"}).status_code == 401


def test_google_start_requires_config(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
    assert client.get("/auth/google/start", follow_redirects=False).status_code == 503


def test_google_login_callback_mints_code_without_creating_account(client, monkeypatch):
    # Configure + stub the Google exchange and JWKS verification.
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

    from app.oauth import google_flow, state as oauth_state

    class _Result:
        id_token = "fake-google-jwt"
    monkeypatch.setattr(google_flow, "exchange_code", lambda **k: _Result())
    monkeypatch.setattr(
        login_google.auth_providers, "verify_google",
        lambda id_token: ("google-sub-xyz", "parent@gmail.com", True),
    )

    # Forge a login-state token as /auth/google/start would.
    state = oauth_state.sign_state({"login": True, "surface": "ios", "cv": "verifier"})
    resp = client.get(f"/oauth/google/callback?code=abc&state={state}", follow_redirects=False)
    assert resp.status_code in (302, 307)
    loc = resp.headers["location"]
    assert loc.startswith("mvparent://auth?")
    assert "status=success" in loc and "login_code=" in loc

    # Account creation is DEFERRED to /auth/exchange-code — the callback must NOT
    # have created an identity yet (so the exchange can claim a legacy account).
    assert server.storage_backend.get_identity("google", "google-sub-xyz") is None


# ── Pairing code (phone → dashboard) ─────────────────────────────────────────

def test_pairing_code_round_trip(client):
    # Authenticate as a user (legacy token is fine) and mint a pairing code.
    token = client.post("/auth/issue-token", json={"user_id": "pair-user"}).json()["token"]
    made = client.post("/auth/pairing-code", headers={"Authorization": f"Bearer {token}"})
    assert made.status_code == 200, made.text
    code = made.json()["code"]

    # The dashboard redeems it for a full session.
    logged = client.post("/auth/pairing-login", json={"code": code})
    assert logged.status_code == 200, logged.text
    assert logged.json()["user_id"] == "pair-user"

    # Single use.
    assert client.post("/auth/pairing-login", json={"code": code}).status_code == 401


def test_pairing_login_rejects_bad_code(client):
    assert client.post("/auth/pairing-login", json={"code": "NOPE-NOPE"}).status_code == 401
