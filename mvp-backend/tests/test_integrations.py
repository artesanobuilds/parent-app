"""
Tests for the R5 multi-provider integration layer: token encryption,
integration_accounts storage CRUD + cascade, the provider registry, and the
Google adapters (via an injected fake service — no live OAuth/SDK calls).
Fully hermetic.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.integrations import crypto  # noqa: E402
from app.integrations.base import CalendarEvent, OAuthCredentials  # noqa: E402
from app.integrations.registry import (  # noqa: E402
    get_calendar_provider,
    get_email_provider,
)


# ── crypto ───────────────────────────────────────────────────────────────────

def test_token_encrypt_roundtrip_and_tamper():
    secret = "1//refresh-token-abc.DEF_ghi"
    ct = crypto.encrypt_token(secret)
    assert ct != secret
    assert crypto.decrypt_token(ct) == secret
    with pytest.raises(ValueError):
        crypto.decrypt_token("not-a-valid-token")


# ── storage ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "integ.duckdb")


def test_integration_account_crud_upsert_revoke_and_isolation(store):
    aid = store.upsert_integration_account(
        "u1", provider="google", kind="email",
        encrypted_refresh_token=crypto.encrypt_token("tok-1"),
        account_email="parent@example.com", scopes="gmail.readonly",
    )
    got = store.get_integration_account("u1", "google", "email")
    assert got["id"] == aid
    assert got["account_email"] == "parent@example.com"
    assert got["status"] == "connected"
    assert crypto.decrypt_token(got["encrypted_refresh_token"]) == "tok-1"

    # Re-auth replaces the row in place (refresh the token), same triple.
    aid2 = store.upsert_integration_account(
        "u1", provider="google", kind="email",
        encrypted_refresh_token=crypto.encrypt_token("tok-2"),
    )
    assert aid2 != aid
    rows = store.list_integration_accounts("u1")
    assert len(rows) == 1  # not duplicated
    assert crypto.decrypt_token(rows[0]["encrypted_refresh_token"]) == "tok-2"

    # A separate kind (calendar) is its own row.
    store.upsert_integration_account(
        "u1", provider="google", kind="calendar",
        encrypted_refresh_token=crypto.encrypt_token("cal-tok"),
    )
    assert len(store.list_integration_accounts("u1")) == 2

    # Revoke scrubs the token + flips status.
    store.revoke_integration_account("u1", "google", "email")
    revoked = store.get_integration_account("u1", "google", "email")
    assert revoked["status"] == "revoked"
    assert revoked["encrypted_refresh_token"] == ""
    assert revoked["revoked_at"] is not None
    assert len(store.list_integration_accounts("u1", status="connected")) == 1

    # Cross-user isolation.
    assert store.get_integration_account("other", "google", "email") is None


def test_delete_family_cascades_integration_accounts(store):
    store.upsert_integration_account(
        "u1", provider="google", kind="email",
        encrypted_refresh_token=crypto.encrypt_token("t"),
    )
    out = store.delete_family(user_id="u1", actor="test")
    assert out["counts"].get("integration_accounts") == 1
    assert store.list_integration_accounts("u1") == []


# ── registry ─────────────────────────────────────────────────────────────────

def _creds():
    return OAuthCredentials(refresh_token="r", scopes=["s"], account_email="a@b.c")


def test_registry_resolves_google_and_rejects_unknown():
    from app.integrations.google import GoogleCalendarProvider, GoogleEmailProvider

    assert isinstance(get_email_provider("google", _creds()), GoogleEmailProvider)
    assert isinstance(get_calendar_provider("google", _creds()), GoogleCalendarProvider)
    with pytest.raises(ValueError):
        get_email_provider("outlook", _creds())
    with pytest.raises(ValueError):
        get_calendar_provider("icloud", _creds())


# ── Google Gmail adapter (injected fake service) ─────────────────────────────

def _b64url(s: str) -> str:
    import base64
    return base64.urlsafe_b64encode(s.encode()).decode()


def test_gmail_list_and_fetch_parse():
    full_msg = {
        "id": "m1",
        "snippet": "Camp HBG welcome see https://camphbg.test/reg",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "Carey <carey@camphbg.test>"},
                {"name": "Subject", "value": "Welcome to Camp HBG"},
                {"name": "Date", "value": "Mon, 1 Jun 2026 09:00:00 -0700"},
            ],
            "body": {"data": _b64url("Register at https://camphbg.test/reg by July 1.")},
        },
    }
    svc = MagicMock()
    messages = svc.users.return_value.messages.return_value
    messages.list.return_value.execute.return_value = {"messages": [{"id": "m1"}]}
    messages.get.return_value.execute.return_value = full_msg

    provider = get_email_provider("google", _creds(), service=svc)

    listed = provider.list_messages(query="camp", since="2026-05-01", max_results=10)
    assert len(listed) == 1
    assert listed[0].sender == "Carey <carey@camphbg.test>"
    assert listed[0].subject == "Welcome to Camp HBG"

    full = provider.fetch_message("m1")
    assert "Register at" in full.body_text
    assert "https://camphbg.test/reg" in full.links

    # Gmail query was composed with the after: filter (YYYY/MM/DD).
    _, kwargs = messages.list.call_args
    assert "after:2026/05/01" in kwargs["q"]
    assert kwargs["maxResults"] == 10


# ── Google Calendar adapter (injected fake service) ──────────────────────────

def test_gcal_push_pull_delete():
    svc = MagicMock()
    events = svc.events.return_value
    events.insert.return_value.execute.return_value = {"id": "evt-new"}
    events.update.return_value.execute.return_value = {"id": "evt-upd"}
    events.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "g1",
                "summary": "Art Camp",
                "location": "Healdsburg",
                "start": {"date": "2026-07-06"},
                "end": {"date": "2026-07-11"},
            }
        ]
    }
    provider = get_calendar_provider("google", _creds(), service=svc)

    # Insert when no provider id.
    new_id = provider.push_event(CalendarEvent(title="Art Camp", start="2026-07-06", all_day=True))
    assert new_id == "evt-new"
    body = events.insert.call_args.kwargs["body"]
    assert body["summary"] == "Art Camp"
    assert body["start"] == {"date": "2026-07-06"}

    # Update when provider id present.
    upd_id = provider.push_event(
        CalendarEvent(title="Art Camp", start="2026-07-06", all_day=True, provider_event_id="g1")
    )
    assert upd_id == "evt-upd"
    assert events.update.call_args.kwargs["eventId"] == "g1"

    # Pull parses items → CalendarEvent.
    pulled = provider.pull_events(since="2026-06-01T00:00:00Z")
    assert len(pulled) == 1
    assert pulled[0].title == "Art Camp"
    assert pulled[0].all_day is True
    assert pulled[0].provider_event_id == "g1"

    provider.delete_event("g1")
    assert events.delete.call_args.kwargs["eventId"] == "g1"
