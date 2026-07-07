"""Crisis-lock push (app/push) + device-token storage.

APNs is env-gated: disabled by default (a no-op), armed only when APNS_* are set.
No network — we test token storage, gating, and the ES256 JWT signing offline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "push.duckdb")


def test_push_token_roundtrip_idempotent(store):
    store.save_push_token(user_id="u1", token="tokA")
    store.save_push_token(user_id="u1", token="tokA")  # re-register → no dup
    store.save_push_token(user_id="u1", token="tokB")
    assert sorted(store.list_push_tokens("u1")) == ["tokA", "tokB"]
    assert store.list_push_tokens("other") == []
    store.delete_push_token("tokA")
    assert store.list_push_tokens("u1") == ["tokB"]


def test_delete_family_cascades_push_tokens(store):
    store.save_push_token(user_id="u1", token="tokA")
    store.delete_family(user_id="u1", actor="test")
    assert store.list_push_tokens("u1") == []


def test_push_disabled_by_default_is_noop():
    # Fresh import with no APNS_* env → disabled; send is a silent no-op.
    import importlib
    import app.push as push
    importlib.reload(push)
    assert push.is_enabled() is False
    push.send_crisis_push(storage=None, user_id="u1", kid_name="Kid", agent_id="a1")  # must not raise


def test_push_arms_and_signs_es256_jwt(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    monkeypatch.setenv("APNS_KEY_ID", "KEY1234567")
    monkeypatch.setenv("APNS_TEAM_ID", "TEAM123456")
    monkeypatch.setenv("APNS_BUNDLE_ID", "MVP.MVParent")
    monkeypatch.setenv("APNS_AUTH_KEY", pem)
    import importlib
    import app.push as push
    importlib.reload(push)
    assert push.init_push() is True
    assert push.is_enabled() is True
    jwt = push._provider_jwt()
    assert jwt.count(".") == 2 and len(jwt) > 100
    # cached on second call
    assert push._provider_jwt() == jwt
    importlib.reload(push)  # reset global state for other tests
