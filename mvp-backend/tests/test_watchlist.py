"""Phase 4: registration-window watchlist — the notification-SLO tests.

Covers the pure due-time transition matrix (tz-aware, known/unknown time,
notify-before-never-after), snapshot re-arm on date change, the worker's
durable-first delivery (row + fallback to-do exist even when every push
fails; outcomes recorded; retry inside grace; escalation after), the close
pass vs the miss detector, the creation service's date normalization + trust
rules, lifecycle auto-create, board join, and the cascades. Hermetic —
tempfile DuckDB, fake send function, injected clocks.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cos import lifecycle  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.watchlist import windows as W  # noqa: E402
from app.watchlist.service import maybe_watch_from_activity, watch_registration  # noqa: E402
from app.watchlist.worker import WatchlistWorker  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "watchlist.duckdb")


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


# ── due-time transition matrix (pure) ────────────────────────────────

# Time KNOWN: opens 2026-08-12 17:00 UTC (10:00 PT). day_of due 16:00–17:00 UTC.
KNOWN = {"opens_at": "2026-08-12T17:00:00+00:00", "opens_time_known": True,
         "tz": "America/Los_Angeles"}
# Time UNKNOWN: opens "Aug 12" local (stored as local midnight = 07:00 UTC).
# day_of due Aug 11 18:00 PT = Aug 12 01:00 UTC, until opens (Aug 12 07:00 UTC).
UNKNOWN = {"opens_at": "2026-08-12T00:00:00-07:00", "opens_time_known": False,
           "tz": "America/Los_Angeles"}


@pytest.mark.parametrize("window,now,expected", [
    # Known time: before any band → nothing.
    (KNOWN, "2026-08-01T00:00:00", None),
    # Inside T-7 band.
    (KNOWN, "2026-08-06T00:00:00", W.T_MINUS_7),
    # Inside the 1h day-of lead.
    (KNOWN, "2026-08-12T16:30:00", W.DAY_OF),
    # AFTER opening: never notify late.
    (KNOWN, "2026-08-12T17:05:00", None),
    # Unknown time: evening before, local (Aug 12 02:00 UTC = Aug 11 19:00 PT).
    (UNKNOWN, "2026-08-12T02:00:00", W.DAY_OF),
    # Unknown time: after local midnight → too late.
    (UNKNOWN, "2026-08-12T08:00:00", None),
    # Unknown time, T-7 band (Aug 5, mid-day UTC).
    (UNKNOWN, "2026-08-05T12:00:00", W.T_MINUS_7),
    # day_of WINS over t_minus_7 once its band starts (never both).
    (KNOWN, "2026-08-12T16:59:00", W.DAY_OF),
])
def test_due_kind_matrix(window, now, expected):
    assert W.due_kind(window, _utc(now)) == expected


def test_no_opens_at_is_never_due():
    assert W.due_kind({"opens_at": None}, _utc("2026-08-01T00:00:00")) is None


# ── the creation service ─────────────────────────────────────────────

def _seed_profile(user_id: str) -> None:
    from app.profiling import profiling_service
    profiling_service._profiles.pop(user_id, None)  # type: ignore[attr-defined]
    profiling_service.update_parent_profile(
        user_id, {"name": "Pat", "postal_code": "95448", "country": "US"}
    )


def test_watch_registration_date_only_is_local_midnight(store):
    _seed_profile("w1")
    window = watch_registration(store, "w1", opens_at="2026-08-12")
    assert window["status"] == "watching"
    assert window["opens_time_known"] is False
    assert window["tz"] == "America/Los_Angeles"
    opens = W.parse_ts(window["opens_at"])
    # Local midnight PDT == 07:00 UTC — NOT bare UTC midnight (day drift).
    assert opens == _utc("2026-08-12T07:00:00")


def test_watch_registration_datetime_keeps_time(store):
    _seed_profile("w2")
    window = watch_registration(store, "w2", opens_at="2026-08-12T10:00:00-07:00")
    assert window["opens_time_known"] is True


def test_agent_research_is_always_estimated(store):
    _seed_profile("w3")
    window = watch_registration(
        store, "w3", opens_at="2026-08-12", source="agent_research",
        confidence="confirmed",  # even an explicit confirmed is overridden
    )
    assert window["confidence"] == "estimated"


def test_bad_opens_at_raises(store):
    _seed_profile("w4")
    with pytest.raises(ValueError):
        watch_registration(store, "w4", opens_at="sometime in august")


# ── worker: durable-first delivery + retry + close + miss ────────────

def _mk_worker(store, outcomes):
    """Worker with a scripted send: pops outcomes per call ('sent'/'failed')."""
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        return outcomes.pop(0) if outcomes else "sent"

    return WatchlistWorker(store, send_fn=send), calls


def test_sweep_delivers_durable_first_even_when_push_fails(store):
    _seed_profile("u1")
    window = watch_registration(store, "u1", opens_at="2026-08-12")
    worker, calls = _mk_worker(store, ["failed"])

    # Inside the T-7 band.
    stats = worker.sweep(now=_utc("2026-08-06T12:00:00"))
    assert stats["delivered"] == 1 and len(calls) == 1

    # Durable floor: the log row AND the fallback to-do exist despite failure.
    rows = store.list_window_notifications(window["id"])
    assert len(rows) == 1 and rows[0]["outcome"] == "failed"
    todos = [t for t in store.list_todos("u1") if t.get("source") == "watchlist"]
    assert len(todos) == 1

    # Idempotent: a second sweep at the same moment retries the FAILED row
    # (still inside grace) but never inserts a second one.
    worker2, _ = _mk_worker(store, ["sent"])
    stats2 = worker2.sweep(now=_utc("2026-08-06T12:05:00"))
    assert stats2["delivered"] == 0 and stats2["retried"] == 1
    rows = store.list_window_notifications(window["id"])
    assert len(rows) == 1 and rows[0]["outcome"] == "sent"


def test_date_change_rearms_notifications(store):
    _seed_profile("u2")
    window = watch_registration(store, "u2", opens_at="2026-08-12")
    worker, _ = _mk_worker(store, ["sent"])
    worker.sweep(now=_utc("2026-08-06T12:00:00"))
    assert len(store.list_window_notifications(window["id"])) == 1

    # Registration moved: new opens_at = new snapshot → T-7 fires again.
    store.update_registration_window(window["id"], opens_at="2026-08-19T07:00:00+00:00")
    worker2, _ = _mk_worker(store, ["sent"])
    stats = worker2.sweep(now=_utc("2026-08-13T12:00:00"))
    assert stats["delivered"] == 1
    assert len(store.list_window_notifications(window["id"])) == 2


def test_escalation_after_grace_and_close_pass(store):
    _seed_profile("u3")
    window = watch_registration(store, "u3", opens_at="2026-08-12")
    worker, _ = _mk_worker(store, ["failed"])
    worker.sweep(now=_utc("2026-08-12T02:00:00"))  # day_of band (eve before, local)

    # Past opens + grace: the failed row is escalated exactly once…
    late = _utc("2026-08-12T12:00:00")  # 05:00 PT, past local midnight + 2h grace
    worker3, _ = _mk_worker(store, [])
    stats = worker3.sweep(now=late)
    assert stats["escalated"] == 1
    rows = store.list_window_notifications(window["id"])
    assert rows[0]["outcome"] == "failed_final"
    # …and the window closes (day_of row exists for the snapshot).
    assert store.get_registration_window(window["id"])["status"] == "closed"


def test_miss_detector_counts_unnotified_opened_windows(store):
    _seed_profile("u4")
    watch_registration(store, "u4", opens_at="2020-01-01")  # long past, no rows
    assert store.count_missed_windows() == 1


# ── lifecycle auto-create + board join ───────────────────────────────

def test_autocreate_from_activity_details(store):
    _seed_profile("u5")
    aid = store.track_activity(
        "u5", name="River Camp", activity_type="camp",
        details={"registration_opens_at": "2026-08-12"},
    )
    activity = store.get_tracked_activity(aid)
    maybe_watch_from_activity(store, "u5", activity)
    windows = store.list_registration_windows("u5", status="watching")
    assert len(windows) == 1 and windows[0]["activity_id"] == aid
    assert windows[0]["confidence"] == "estimated"  # researched, not stated

    # Idempotent: a second call must not create a twin.
    maybe_watch_from_activity(store, "u5", activity)
    assert len(store.list_registration_windows("u5", status="watching")) == 1


def test_outing_never_autocreates(store):
    _seed_profile("u6")
    aid = store.track_activity(
        "u6", name="Tide Pools", activity_type="outing",
        details={"registration_opens_at": "2026-08-12"},
    )
    maybe_watch_from_activity(store, "u6", store.get_tracked_activity(aid))
    assert store.list_registration_windows("u6") == []


def test_board_carries_the_window_line(store):
    _seed_profile("u7")
    aid = store.track_activity("u7", name="River Camp", activity_type="camp")
    watch_registration(store, "u7", opens_at="2026-08-12", activity_id=aid)
    board = lifecycle.build_board(
        store.list_tracked_activities("u7"), [],
        registration_windows=store.list_registration_windows("u7", status="watching"),
    )
    cards = [a for s in board["stages"] for a in s["activities"]]
    rw = cards[0]["registration_window"]
    assert rw is not None
    assert rw["line"] == "Registration opens Aug 12 · watching"


# ── cascades ─────────────────────────────────────────────────────────

def test_delete_activity_cascades_windows(store):
    _seed_profile("u8")
    aid = store.track_activity("u8", name="Doomed Camp", activity_type="camp")
    window = watch_registration(store, "u8", opens_at="2026-08-12", activity_id=aid)
    worker, _ = _mk_worker(store, ["sent"])
    worker.sweep(now=_utc("2026-08-06T12:00:00"))

    store.delete_tracked_activity(aid)
    assert store.get_registration_window(window["id"]) is None
    assert store.list_window_notifications(window["id"]) == []


def test_reset_plan_and_delete_family_cascade(store):
    _seed_profile("u9")
    watch_registration(store, "u9", opens_at="2026-08-12")
    store.reset_plan(user_id="u9", actor="test")
    assert store.list_registration_windows("u9") == []

    _seed_profile("u10")
    window = watch_registration(store, "u10", opens_at="2026-08-12")
    worker, _ = _mk_worker(store, ["sent"])
    worker.sweep(now=_utc("2026-08-06T12:00:00"))
    store.delete_family(user_id="u10", actor="test")
    assert store.list_registration_windows("u10") == []
    assert store.list_window_notifications(window["id"]) == []
