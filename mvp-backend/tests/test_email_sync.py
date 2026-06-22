"""
Tests for the R3 daily Gmail-sync agent: per-user `run_email_sync` (emails from a
registered camp attach to that activity, idempotent), the `materialize(
link_activity_id=…)` behavior, and the `EmailSyncWorker` schedule tick + run
processing. Hermetic — temp DuckDB, fake EmailProvider, mocked extractor.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.integrations import crypto  # noqa: E402
from app.integrations.base import IngestMessage  # noqa: E402
from app.ingest.extract import ExtractedActivity  # noqa: E402
from app.email_sync import sync as email_sync  # noqa: E402
from app.email_sync.worker import EmailSyncWorker  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "esync.duckdb")


class _FakeProvider:
    def __init__(self, messages, fulls):
        self.messages = messages
        self.fulls = fulls
        self.queries = []

    def list_messages(self, *, query=None, since=None, max_results=25):
        self.queries.append(query)
        return self.messages

    def fetch_message(self, mid):
        return self.fulls[mid]


def _connect_email(store, user_id="u1"):
    store.upsert_integration_account(
        user_id, provider="google", kind="email",
        encrypted_refresh_token=crypto.encrypt_token("tok"),
        account_email="parent@example.com", scopes="gmail.readonly",
    )


def test_run_email_sync_attaches_to_registered_and_is_idempotent(store, monkeypatch):
    _connect_email(store)
    # A registered camp with a known contact email.
    act_id = store.track_activity(
        "u1", name="Camp HBG", status="confirmed",
        contact={"email": "carey@camphbg.test", "name": "Carey"},
    )

    provider = _FakeProvider(
        messages=[IngestMessage(id="m1", sender="Carey <carey@camphbg.test>")],
        fulls={
            "m1": IngestMessage(
                id="m1", sender="Carey <carey@camphbg.test>",
                subject="Payment due", body_text="Pay $200 by July 1.",
                received_at="2026-06-20T09:00:00Z",
            )
        },
    )
    # No LLM: run_email_sync imports app.ingest.extract lazily, so patch there.
    import app.ingest.extract as extract_mod
    monkeypatch.setattr(
        extract_mod, "extract_from_text",
        lambda *a, **k: ExtractedActivity(
            provider="Camp HBG", dates=["2026-07-06"], amount_due=200.0,
            payment_due_date="2026-07-01", action_items=["Pay $200"],
        ),
    )

    out = email_sync.run_email_sync(store, "u1", provider=provider)
    assert out["messages_seen"] == 1 and out["activities_touched"] == 1
    # Gmail query targeted the camp's address/domain + window.
    assert "carey@camphbg.test" in provider.queries[0]
    assert "newer_than" in provider.queries[0]
    # The run detail records the search + per-message result for the CMS view.
    assert out["detail"]["query"] == provider.queries[0]
    assert len(out["detail"]["items"]) == 1
    item = out["detail"]["items"][0]
    assert item["matched"] == "Camp HBG" and item["action"] == "ingested"
    assert item["created"]["todos"] >= 1

    # NO new tracked activity — the email attached to the registered one.
    acts = store.list_tracked_activities("u1")
    assert len(acts) == 1 and acts[0]["id"] == act_id
    # Calendar entry + to-dos were linked to that activity.
    cal = store.list_calendar_entries("u1") if hasattr(store, "list_calendar_entries") else []
    assert any(e.get("activity_id") == act_id for e in cal)
    todos = store.list_todos("u1")
    assert any("Pay" in t["title"] for t in todos)
    todos_before = len(todos)

    # Re-run: idempotent — message already ingested (external_id), nothing new.
    out2 = email_sync.run_email_sync(store, "u1", provider=provider)
    assert out2["messages_seen"] == 0
    assert len(store.list_todos("u1")) == todos_before
    assert len(store.list_ingest_artifacts("u1")) == 1


def test_run_email_sync_noop_without_registered_or_account(store):
    # No connected account.
    out = email_sync.run_email_sync(store, "u1", provider=_FakeProvider([], {}))
    assert out["messages_seen"] == 0 and out["activities_touched"] == 0
    assert out["detail"]["note"] == "no connected Gmail account"
    # Connected but no registered camps → no query made, with an explanatory note.
    _connect_email(store)
    p = _FakeProvider([], {})
    out2 = email_sync.run_email_sync(store, "u1", provider=p)
    assert out2["messages_seen"] == 0
    assert p.queries == []  # never queried — nothing to match
    assert "no registered camps" in out2["detail"]["note"]


def test_worker_schedule_tick_enqueues_once_per_day(store):
    _connect_email(store, "u1")
    _connect_email(store, "u2")
    store.set_agent_config("email_sync_schedule", {"enabled": True, "hour": 6, "tz": "UTC"})
    w = EmailSyncWorker(store, sync_fn=lambda *a, **k: {"messages_seen": 0, "activities_touched": 0})

    at6 = datetime(2026, 6, 22, 6, 30, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=at6) == 2          # one run per connected account
    assert w.maybe_schedule(now=at6) == 0          # guard: already scheduled today
    at7 = datetime(2026, 6, 22, 7, 0, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=at7) == 0          # wrong hour
    nextday = datetime(2026, 6, 23, 6, 5, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=nextday) == 2      # new day → schedules again

    # Disabled → never schedules.
    store.set_agent_config("email_sync_schedule", {"enabled": False, "hour": 6, "tz": "UTC"})
    assert w.maybe_schedule(now=datetime(2026, 6, 24, 6, 0, tzinfo=timezone.utc)) == 0


def test_worker_process_run_marks_done(store):
    rid = store.create_email_sync_run(user_id="u1", trigger="manual")
    run = store.claim_next_queued_email_sync_run()
    w = EmailSyncWorker(store, sync_fn=lambda *a, **k: {"messages_seen": 4, "activities_touched": 2})
    w.process_run(run)
    done = store.get_email_sync_run(rid)
    assert done["status"] == "done"
    assert done["messages_seen"] == 4 and done["activities_touched"] == 2


def test_worker_process_run_marks_failed(store):
    rid = store.create_email_sync_run(user_id="u1", trigger="manual")
    run = store.claim_next_queued_email_sync_run()

    def _boom(*a, **k):
        raise RuntimeError("gmail exploded")

    EmailSyncWorker(store, sync_fn=_boom).process_run(run)
    failed = store.get_email_sync_run(rid)
    assert failed["status"] == "failed"
    assert "gmail exploded" in failed["error"]
