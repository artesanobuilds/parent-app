"""
Tests for R4 part 2 — two-way Google Calendar sync. Covers the per-user
`run_calendar_sync` (push owned entries + stamp the event id, idempotent re-runs,
re-push on local edit; pull external events as source='gcal', skip our own echo,
update an existing import) and the `CalendarSyncWorker` schedule tick + run
processing. Hermetic — temp DuckDB, fake CalendarProvider, no network.
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
from app.integrations.base import CalendarEvent  # noqa: E402
from app.calendar_sync import sync as calendar_sync  # noqa: E402
from app.calendar_sync.worker import CalendarSyncWorker  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "csync.duckdb")


class _FakeCalendarProvider:
    """Records pushes and serves a canned pull list. push_event returns a stable
    id per event (so update re-pushes target the same id)."""

    def __init__(self, pull=None):
        self.pushed = []          # list of (event_id, CalendarEvent)
        self.deleted = []
        self._pull = list(pull or [])
        self._counter = 0

    def push_event(self, event: CalendarEvent) -> str:
        if event.provider_event_id:
            eid = event.provider_event_id
        else:
            self._counter += 1
            eid = f"gev-{self._counter}"
        self.pushed.append((eid, event))
        return eid

    def pull_events(self, *, since=None, until=None):
        return self._pull

    def delete_event(self, provider_event_id: str) -> None:
        self.deleted.append(provider_event_id)


def _connect_calendar(store, user_id="u1"):
    store.upsert_integration_account(
        user_id, provider="google", kind="calendar",
        encrypted_refresh_token=crypto.encrypt_token("tok"),
        account_email="parent@example.com",
        scopes="https://www.googleapis.com/auth/calendar.events",
    )


def test_push_stamps_event_id_and_is_idempotent(store):
    _connect_calendar(store)
    eid = store.add_calendar_entry(
        "u1", title="Camp HBG", start_ts="2026-07-06T09:00:00Z",
        end_ts="2026-07-06T15:00:00Z", kid_name="Ceiba", source="cos_agent",
    )
    p = _FakeCalendarProvider()

    out = calendar_sync.run_calendar_sync(store, "u1", provider=p)
    assert out["pushed"] == 1 and out["pulled"] == 0
    assert len(p.pushed) == 1
    pushed_id, ev = p.pushed[0]
    assert ev.title == "Camp HBG" and ev.provider_event_id is None  # first push = create
    # The entry now carries the provider event id + synced_at.
    row = store.get_calendar_entry(eid)
    assert row["provider_event_id"] == pushed_id and row["synced_at"]
    assert out["detail"]["pushed_items"][0]["action"] == "created"

    # Re-run with no local change → nothing to push.
    out2 = calendar_sync.run_calendar_sync(store, "u1", provider=_FakeCalendarProvider())
    assert out2["pushed"] == 0


def test_local_edit_repushes_as_update(store):
    _connect_calendar(store)
    eid = store.add_calendar_entry(
        "u1", title="Swim", start_ts="2026-07-06T09:00:00Z", source="manual",
    )
    calendar_sync.run_calendar_sync(store, "u1", provider=_FakeCalendarProvider())
    first = store.get_calendar_entry(eid)["provider_event_id"]

    # Parent edits the entry → updated_at bumps past synced_at → dirty again.
    store.update_calendar_entry(eid, title="Swim Lessons")
    p = _FakeCalendarProvider()
    out = calendar_sync.run_calendar_sync(store, "u1", provider=p)
    assert out["pushed"] == 1
    pushed_id, ev = p.pushed[0]
    assert pushed_id == first                       # same Google event, updated in place
    assert ev.provider_event_id == first            # update path carried the id
    assert ev.title == "Swim Lessons"
    assert out["detail"]["pushed_items"][0]["action"] == "updated"


def test_pull_imports_external_and_skips_our_echo(store):
    _connect_calendar(store)
    # One of ours (already pushed) + one external event the parent owns.
    eid = store.add_calendar_entry(
        "u1", title="Camp", start_ts="2026-07-06T09:00:00Z", source="cos_agent",
    )
    store.mark_calendar_pushed(eid, "gev-ours")

    pull = [
        CalendarEvent(  # our own event coming back — must be skipped
            title="Camp", start="2026-07-06T09:00:00Z", provider_event_id="gev-ours",
        ),
        CalendarEvent(  # a genuinely external commitment
            title="Dentist", start="2026-07-08T10:00:00Z",
            end="2026-07-08T11:00:00Z", location="Main St",
            provider_event_id="gev-ext-1",
        ),
    ]
    out = calendar_sync.run_calendar_sync(store, "u1", provider=_FakeCalendarProvider(pull=pull))
    assert out["pulled"] == 1
    entries = store.list_calendar_entries("u1")
    external = [e for e in entries if e["source"] == "gcal"]
    assert len(external) == 1
    assert external[0]["title"] == "Dentist" and external[0]["kind"] == "external"
    assert external[0]["provider_event_id"] == "gev-ext-1"
    # The skipped echo did NOT create a duplicate of our camp.
    assert sum(1 for e in entries if e["title"] == "Camp") == 1

    # Re-pull the same external event → updates in place, no duplicate.
    out2 = calendar_sync.run_calendar_sync(
        store, "u1",
        provider=_FakeCalendarProvider(pull=[
            CalendarEvent(title="Dentist (moved)", start="2026-07-08T14:00:00Z",
                          provider_event_id="gev-ext-1"),
        ]),
    )
    assert out2["pulled"] == 1
    ext = [e for e in store.list_calendar_entries("u1") if e["source"] == "gcal"]
    assert len(ext) == 1 and ext[0]["title"] == "Dentist (moved)"


def test_pulled_external_is_not_pushed_back(store):
    _connect_calendar(store)
    pull = [CalendarEvent(title="Work meeting", start="2026-07-09T09:00:00Z",
                          provider_event_id="gev-ext-9")]
    calendar_sync.run_calendar_sync(store, "u1", provider=_FakeCalendarProvider(pull=pull))
    # A second run must not try to push the imported (source='gcal') event.
    p = _FakeCalendarProvider()
    out = calendar_sync.run_calendar_sync(store, "u1", provider=p)
    assert out["pushed"] == 0 and p.pushed == []


def test_noop_without_connected_account(store):
    out = calendar_sync.run_calendar_sync(store, "u1", provider=_FakeCalendarProvider())
    assert out["pushed"] == 0 and out["pulled"] == 0
    assert out["detail"]["note"] == "no connected Google Calendar account"


def test_worker_schedule_tick_enqueues_once_per_day(store):
    _connect_calendar(store, "u1")
    _connect_calendar(store, "u2")
    store.set_agent_config("calendar_sync_schedule", {"enabled": True, "hour": 6, "tz": "UTC"})
    w = CalendarSyncWorker(store, sync_fn=lambda *a, **k: {"pushed": 0, "pulled": 0})

    at6 = datetime(2026, 6, 22, 6, 30, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=at6) == 2          # one run per connected account
    assert w.maybe_schedule(now=at6) == 0          # guard: already scheduled today
    at7 = datetime(2026, 6, 22, 7, 0, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=at7) == 0          # wrong hour
    nextday = datetime(2026, 6, 23, 6, 5, tzinfo=timezone.utc)
    assert w.maybe_schedule(now=nextday) == 2      # new day → schedules again


def test_worker_process_run_marks_done_and_failed(store):
    rid = store.create_calendar_sync_run(user_id="u1", trigger="manual")
    run = store.claim_next_queued_calendar_sync_run()
    CalendarSyncWorker(store, sync_fn=lambda *a, **k: {"pushed": 3, "pulled": 2}).process_run(run)
    done = store.get_calendar_sync_run(rid)
    assert done["status"] == "done" and done["pushed"] == 3 and done["pulled"] == 2

    rid2 = store.create_calendar_sync_run(user_id="u1", trigger="manual")
    run2 = store.claim_next_queued_calendar_sync_run()

    def _boom(*a, **k):
        raise RuntimeError("gcal exploded")

    CalendarSyncWorker(store, sync_fn=_boom).process_run(run2)
    failed = store.get_calendar_sync_run(rid2)
    assert failed["status"] == "failed" and "gcal exploded" in failed["error"]
