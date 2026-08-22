"""Admin tester reset (POST /admin/users/{user_id}/reset) — heisman sprint 01
Appendix A1: wipe a tester's family data while KEEPING their sign-in identity,
so Miguel/Heather/Greg can re-run the redesigned onboarding on their real
account (reset → sign out in app → relaunch → funnel → sign in at step 8 →
hasProfile false → continue onboarding on the same user_id).

Covers:
  - reset wipes profiles / chat_threads / tracked_activities
  - auth_identities + user_accounts + legal_acceptances rows SURVIVE
  - a second user is untouched
  - memory singletons evicted (persist_state after reset does not resurrect
    chat_threads — technique from tests/test_delete_memory_eviction.py)
  - audit row "family.reset" written
  - 401 without admin credentials; 404 for an unknown user

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing
app.server, and the storage singleton is rebuilt in teardown (TestClient exit
closes storage — tests/test_admin_session.py pattern).
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

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "admin_reset.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
from app.duckdb_storage import (  # noqa: E402
    FAMILY_CASCADE_TABLES,
    FAMILY_IDENTITY_TABLES,
    FAMILY_RESET_SKIP_TABLES,
)

ADMIN = "test-admin-token-reset"
TESTER = "reset-tester"
BYSTANDER = "reset-bystander"


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app, base_url="https://testserver") as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _count(table: str, user_id: str) -> int:
    return server.storage_backend._con.execute(
        f"SELECT count(*) FROM {table} WHERE user_id = ?", [user_id],
    ).fetchone()[0]


def _seed(user_id: str) -> None:
    storage = server.storage_backend
    storage.get_or_create_account(user_id, primary_email=f"{user_id}@example.com")
    storage.link_identity(
        user_id=user_id, provider="apple", provider_sub=f"sub-{user_id}",
        email=f"{user_id}@example.com", email_verified=True,
    )
    storage.record_legal_acceptance(
        user_id=user_id,
        docs=[{"document_id": "doc-1", "slug": "terms", "version": "1.0"}],
    )
    storage.save_user_data(user_id, "profiles", {"parent": {"name": user_id}})
    storage._con.execute(
        "INSERT INTO tracked_activities (id, user_id, name) VALUES (?, ?, ?)",
        [f"act-{user_id}", user_id, "Soccer camp"],
    )
    # Chat through the in-memory store + persist — the exact write path that
    # can resurrect wiped conversations if eviction is missing.
    server.chat_memory.append_message(user_id, "t-1", "user", "hi coach")
    server.chat_memory.append_message(user_id, "t-1", "assistant", "hey!")
    server.persist_state(user_id)


# --------------------------------------------------------------------------- #
# Partition sanity: delete and reset are built from the SAME list
# --------------------------------------------------------------------------- #


def test_partition_constants_are_consistent():
    assert FAMILY_IDENTITY_TABLES == {
        "auth_identities", "user_accounts", "refresh_tokens", "auth_tokens",
    }
    assert FAMILY_RESET_SKIP_TABLES == FAMILY_IDENTITY_TABLES | {"legal_acceptances"}
    for t in FAMILY_RESET_SKIP_TABLES:
        assert t in FAMILY_CASCADE_TABLES, (
            f"{t} left FAMILY_CASCADE_TABLES — the skip set no longer matches"
        )


# --------------------------------------------------------------------------- #
# Auth gates
# --------------------------------------------------------------------------- #


def test_reset_requires_admin_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    assert client.post(f"/admin/users/{TESTER}/reset").status_code == 401
    assert client.post(
        f"/admin/users/{TESTER}/reset", headers={"X-Admin-Token": "wrong"},
    ).status_code == 401


def test_reset_404_for_unknown_user(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    resp = client.post(
        "/admin/users/no-such-user/reset", headers={"X-Admin-Token": ADMIN},
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# The reset itself
# --------------------------------------------------------------------------- #


def test_reset_wipes_data_keeps_identity_and_bystander(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", ADMIN)
    try:
        _seed(TESTER)
        _seed(BYSTANDER)
        assert server.storage_backend.load_user_data(TESTER, "chat_threads"), (
            "seed failed — persist_state should have written chat_threads"
        )

        resp = client.post(
            f"/admin/users/{TESTER}/reset", headers={"X-Admin-Token": ADMIN},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == TESTER
        assert body["identity_kept"] is True
        assert isinstance(body["counts"], dict)
        assert body["counts"]["user_data"] >= 1
        assert body["counts"]["tracked_activities"] == 1
        # The identity tables never appear in a reset's counts.
        for t in FAMILY_RESET_SKIP_TABLES:
            assert t not in body["counts"]

        # Data gone.
        assert server.storage_backend.load_user_data(TESTER, "profiles") is None
        assert not server.storage_backend.user_has_profile(TESTER)
        assert _count("user_data", TESTER) == 0
        assert _count("tracked_activities", TESTER) == 0
        # Identity + legal acceptance SURVIVE — the whole point of reset.
        assert _count("auth_identities", TESTER) == 1
        assert _count("user_accounts", TESTER) == 1
        assert _count("legal_acceptances", TESTER) == 1
        assert server.storage_backend.user_has_any_identity(TESTER)

        # The bystander is completely untouched.
        assert server.storage_backend.load_user_data(BYSTANDER, "profiles")
        assert _count("tracked_activities", BYSTANDER) == 1
        assert _count("auth_identities", BYSTANDER) == 1
        assert server.storage_backend.load_user_data(BYSTANDER, "chat_threads")

        # Memory singletons evicted: a subsequent FULL persist (any other
        # user's save, any export) must not resurrect the wiped threads.
        server.persist_state()
        assert not server.storage_backend.load_user_data(TESTER, "chat_threads"), (
            "reset user's chat_threads resurrected — the in-memory store "
            "still held the id at persist time"
        )

        # Audit row written, with the reset-specific action.
        rows = server.storage_backend._con.execute(
            "SELECT action FROM audit_events WHERE user_id = ?", [TESTER],
        ).fetchall()
        assert ("family.reset",) in rows
    finally:
        server.chat_memory.remove_user(TESTER)
        server.chat_memory.remove_user(BYSTANDER)
        server.onboarding_memory.remove_user(TESTER)
        server.onboarding_memory.remove_user(BYSTANDER)
