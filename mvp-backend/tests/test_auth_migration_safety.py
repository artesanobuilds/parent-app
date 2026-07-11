"""Migration safety net for existing prod users (founders included).

Covers the two ways an automatic legacy claim fails and the operator recovery:
  1. Happy path: valid legacy token → sign-in claims the existing account.
  2. Expired/missing legacy token → sign-in makes a FRESH account (data orphaned).
  3. admin/link-legacy moves the founder's real identity onto their legacy
     user_id and deletes the empty account — data preserved.
Also the migration-status monitor.
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

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "auth_migration.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-migration")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
import app.auth_router as auth_router  # noqa: E402

ADMIN = "test-admin-migration"


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture
def fake_apple(monkeypatch):
    def _verify(provider, id_token, nonce=None):
        return (f"apple-sub-{id_token}", None, True)
    monkeypatch.setattr(auth_router.auth_providers, "verify", _verify)


def _seed_founder(storage, user_id: str) -> None:
    """A prod-like founder: real family data + a backfilled account row."""
    storage._con.execute(
        "INSERT OR IGNORE INTO user_data (user_id, name, data) VALUES (?, ?, ?)",
        [user_id, user_id, "{}"],
    )
    storage.get_or_create_account(user_id)


# ── 1. Happy path: automatic claim with a valid legacy token ─────────────────

def test_founder_claims_with_valid_legacy_token(client, fake_apple):
    storage = server.storage_backend
    _seed_founder(storage, "Founder Heather")
    legacy = client.post("/auth/issue-token", json={"user_id": "Founder Heather"}).json()["token"]

    res = client.post("/auth/login", json={
        "provider": "apple", "id_token": "heather", "platform": "ios",
        "legacy_user_id": "Founder Heather", "legacy_token": legacy,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["user_id"] == "Founder Heather"     # same account — data preserved
    assert body["linked_legacy"] is True
    assert body["is_new_account"] is False


# ── 2. Failed claim (no/expired token) orphans data onto a fresh account ─────

def test_failed_claim_creates_fresh_account(client, fake_apple):
    storage = server.storage_backend
    _seed_founder(storage, "Founder Miguel")
    # Sign in WITHOUT legacy proof (simulates fresh install / expired token).
    res = client.post("/auth/login", json={"provider": "apple", "id_token": "miguel", "platform": "ios"})
    assert res.status_code == 200
    body = res.json()
    assert body["is_new_account"] is True
    assert body["user_id"] != "Founder Miguel"       # orphaned onto a fresh uuid
    # The Apple sub is now (wrongly) bound to the fresh account.
    ident = storage.get_identity("apple", "apple-sub-miguel")
    assert ident["user_id"] == body["user_id"] != "Founder Miguel"


# ── 3. Admin relink recovers it: identity → real user_id, empty account gone ─

def test_admin_relink_recovers_orphaned_founder(client, fake_apple, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    storage = server.storage_backend
    _seed_founder(storage, "Founder Greg")
    # Failed claim → fresh empty account holds the Apple sub.
    fresh = client.post("/auth/login", json={"provider": "apple", "id_token": "greg"}).json()
    fresh_uid = fresh["user_id"]
    assert storage.get_identity("apple", "apple-sub-greg")["user_id"] == fresh_uid

    # Operator relinks the sub to Greg's real account.
    fix = client.post(
        "/admin/auth/link-legacy",
        headers={"X-Admin-Token": ADMIN},
        json={"provider": "apple", "provider_sub": "apple-sub-greg", "target_user_id": "Founder Greg"},
    )
    assert fix.status_code == 200, fix.text
    out = fix.json()
    assert out["relinked"] is True
    assert out["moved_from"] == fresh_uid
    assert out["deleted_empty_account"] == fresh_uid

    # Identity now points at the real family; the empty account is gone.
    assert storage.get_identity("apple", "apple-sub-greg")["user_id"] == "Founder Greg"
    assert storage.analytics_id_for(fresh_uid) is None            # empty account deleted
    assert storage.analytics_id_for("Founder Greg") is not None   # real account intact

    # Signing in again now lands on the real account.
    again = client.post("/auth/login", json={"provider": "apple", "id_token": "greg"})
    assert again.json()["user_id"] == "Founder Greg"


def test_admin_relink_refuses_to_delete_nonempty_account(client, fake_apple, monkeypatch):
    """If the 'wrong' account somehow has data, relink moves the identity but
    must NOT delete that account (never destroy family data)."""
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    storage = server.storage_backend
    _seed_founder(storage, "Real Target")
    # A non-empty source account.
    _seed_founder(storage, "Has Data Source")
    storage.link_identity(user_id="Has Data Source", provider="google", provider_sub="g-sub-1")

    fix = client.post(
        "/admin/auth/link-legacy",
        headers={"X-Admin-Token": ADMIN},
        json={"provider": "google", "provider_sub": "g-sub-1", "target_user_id": "Real Target"},
    ).json()
    assert fix["moved_from"] == "Has Data Source"
    assert fix["deleted_empty_account"] is None            # NOT deleted — it has data
    assert storage.analytics_id_for("Has Data Source") is not None


# ── 4. Monitor ───────────────────────────────────────────────────────────────

def test_migration_status_reports_claim_state(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    res = client.get("/admin/auth/migration-status", headers={"X-Admin-Token": ADMIN})
    assert res.status_code == 200
    body = res.json()
    assert "total_accounts" in body and "unclaimed" in body and "identities" in body
    # Unauthenticated is refused.
    assert client.get("/admin/auth/migration-status").status_code == 401
