"""Phase 2 auth: JWT lifecycle, refresh rotation + reuse detection, native
login with monkeypatched provider verification, legacy-account claiming,
issue-token retirement, and dual-accept backward compatibility.

The provider JWKS calls are monkeypatched (no network) — same idiom as
tests/test_oauth.py mocking Google.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "auth_v2.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret-for-auth-v2")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
import app.auth as auth  # noqa: E402
import app.auth_router as auth_router  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture
def fake_apple(monkeypatch):
    """Make verify('apple', token) return a fixed identity keyed by the token."""
    def _verify(provider, id_token, nonce=None):
        assert provider == "apple"
        return (f"apple-sub-{id_token}", f"{id_token}@privaterelay.appleid.com", True)
    monkeypatch.setattr(auth_router.auth_providers, "verify", _verify)


# ── JWT lifecycle ────────────────────────────────────────────────────────────

def test_jwt_mint_and_decode_roundtrip():
    token, ttl = auth.mint_access_token("user-abc")
    assert token.count(".") == 2 and ttl > 0
    assert auth._decode_access_token(token) == "user-abc"


def test_jwt_rejects_tamper_and_expiry(monkeypatch):
    token, _ = auth.mint_access_token("user-abc")
    assert auth._decode_access_token(token + "x") is None
    # Expired token.
    monkeypatch.setattr(auth, "_ACCESS_TTL_SECONDS", -10)
    expired, _ = auth.mint_access_token("user-abc")
    assert auth._decode_access_token(expired) is None


# ── Login + session ──────────────────────────────────────────────────────────

def test_login_creates_account_and_authenticates(client, fake_apple):
    r = client.post("/auth/login", json={"provider": "apple", "id_token": "tok1", "platform": "ios"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_new_account"] is True
    assert body["access_token"].count(".") == 2
    assert body["refresh_token"] and body["analytics_id"]
    user_id = body["user_id"]

    # The access token authenticates a protected endpoint (no DB hit).
    prof = client.get("/profile", params={"user_id": user_id},
                      headers={"Authorization": f"Bearer {body['access_token']}"})
    assert prof.status_code == 200

    # Logging in again with the same identity returns the SAME account.
    r2 = client.post("/auth/login", json={"provider": "apple", "id_token": "tok1", "platform": "ios"})
    assert r2.json()["user_id"] == user_id
    assert r2.json()["is_new_account"] is False


def test_analytics_id_is_not_the_user_id(client, fake_apple):
    body = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-distinct"}).json()
    assert body["analytics_id"] != body["user_id"]


def test_has_profile_routes_returning_vs_new(client, fake_apple):
    # Fresh account → no profile → client sends to onboarding.
    first = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-profile"}).json()
    assert first["has_profile"] is False
    user_id = first["user_id"]

    # Seed a profile row, then sign in again (same identity) → has_profile flips
    # true, so a returning user (any device) skips onboarding.
    server.storage_backend._con.execute(
        "INSERT OR IGNORE INTO user_data (user_id, name, data) VALUES (?, ?, ?)",
        [user_id, "profile", "{}"],
    )
    again = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-profile"}).json()
    assert again["user_id"] == user_id
    assert again["has_profile"] is True


# ── Refresh rotation + reuse detection ───────────────────────────────────────

def test_refresh_rotation_and_reuse_nukes_family(client, fake_apple):
    login = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-refresh"}).json()
    rt0 = login["refresh_token"]

    # Rotate → new refresh token; old one is now spent.
    r1 = client.post("/auth/refresh", json={"refresh_token": rt0})
    assert r1.status_code == 200, r1.text
    rt1 = r1.json()["refresh_token"]
    assert rt1 != rt0

    # Reusing the spent rt0 is refused AND revokes the whole lineage.
    reuse = client.post("/auth/refresh", json={"refresh_token": rt0})
    assert reuse.status_code == 401

    # rt1 (the legitimate successor) is now also dead — family nuked.
    after = client.post("/auth/refresh", json={"refresh_token": rt1})
    assert after.status_code == 401


def test_logout_revokes_refresh(client, fake_apple):
    login = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-logout"}).json()
    access = login["access_token"]
    rt = login["refresh_token"]
    out = client.post("/auth/logout", json={"refresh_token": rt},
                      headers={"Authorization": f"Bearer {access}"})
    assert out.status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": rt}).status_code == 401


# ── Legacy claim + issue-token retirement ────────────────────────────────────

def test_legacy_account_claim_preserves_user_id(client, fake_apple):
    # A legacy user exists with an opaque token.
    legacy = client.post("/auth/issue-token", json={"user_id": "legacy-parent-1"})
    assert legacy.status_code == 200
    legacy_token = legacy.json()["token"]

    # Claim it via sign-in: same user_id, identity now bound.
    claimed = client.post("/auth/login", json={
        "provider": "apple", "id_token": "tok-legacy",
        "legacy_user_id": "legacy-parent-1", "legacy_token": legacy_token,
    })
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["user_id"] == "legacy-parent-1"
    assert claimed.json()["linked_legacy"] is True
    assert claimed.json()["is_new_account"] is False


def test_issue_token_refused_once_claimed(client, fake_apple):
    client.post("/auth/issue-token", json={"user_id": "legacy-parent-2"})
    # sign in without a legacy token → fresh uuid account, but bind identity to
    # 'legacy-parent-2'? No — without legacy proof it creates a new account.
    # So claim it properly first:
    lt = client.post("/auth/issue-token", json={"user_id": "legacy-parent-2"}).json()["token"]
    client.post("/auth/login", json={
        "provider": "apple", "id_token": "tok-legacy-2",
        "legacy_user_id": "legacy-parent-2", "legacy_token": lt,
    })
    # Now issue-token for that name is refused.
    refused = client.post("/auth/issue-token", json={"user_id": "legacy-parent-2"})
    assert refused.status_code == 403


def test_issue_token_gone_when_disabled(client, monkeypatch):
    monkeypatch.setenv("AUTH_ISSUE_TOKEN_ENABLED", "0")
    r = client.post("/auth/issue-token", json={"user_id": "whoever"})
    assert r.status_code == 410


def test_legacy_opaque_token_still_authenticates(client):
    # Dual-accept: a legacy opaque token keeps working on protected endpoints
    # (the entire pre-existing test suite proves this too).
    token = client.post("/auth/issue-token", json={"user_id": "dual-accept-user"}).json()["token"]
    prof = client.get("/profile", params={"user_id": "dual-accept-user"},
                      headers={"Authorization": f"Bearer {token}"})
    assert prof.status_code == 200


def test_legacy_tokens_can_be_disabled(client, monkeypatch):
    token = client.post("/auth/issue-token", json={"user_id": "toggle-user"}).json()["token"]
    monkeypatch.setenv("AUTH_LEGACY_TOKENS_ENABLED", "0")
    prof = client.get("/profile", params={"user_id": "toggle-user"},
                      headers={"Authorization": f"Bearer {token}"})
    assert prof.status_code == 401


def test_delete_family_revokes_refresh_tokens(client, fake_apple):
    login = client.post("/auth/login", json={"provider": "apple", "id_token": "tok-del"}).json()
    user_id, access, rt = login["user_id"], login["access_token"], login["refresh_token"]
    dele = client.delete(f"/family/{user_id}", headers={"Authorization": f"Bearer {access}"})
    assert dele.status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": rt}).status_code == 401
