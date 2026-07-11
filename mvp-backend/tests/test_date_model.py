"""
Phase 2 of the vertical expansion: the generalized date model, scoped to
week_block + recurring_weekly.

Covers the v17 migration backfill (idempotent; end_date fabricated = start+4d),
the SINGLE date write path (`set_activity_dates`: week_start derived for
week_block, rrule as recurrence source of truth with the derived
recurring_appointments row regenerated — never hand-edited), the two plan
invariants (week_block => week_start == start_date; recurring_weekly => rrule
NOT NULL), weekly-only RRULE validation, `format_when` board rendering, and
the coverage rule (linked entries decide by vertical capability; unlinked +
gcal entries keep the kind-set fallback — the before/after snapshot).
Hermetic — tempfile DuckDB, no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cos import lifecycle, planning, verticals  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.migrations import _add_tracked_activity_dates  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "phase2.duckdb")


# ── v17 migration backfill ───────────────────────────────────────────


def test_v17_backfill_fabricates_end_date_and_is_idempotent(store):
    aid = store.track_activity("u1", name="Legacy Camp", week_start="2026-07-13")
    # Simulate a pre-v17 row: NULL the new columns the write path set.
    store._con.execute(
        "UPDATE tracked_activities SET start_date = NULL, end_date = NULL WHERE id = ?",
        [aid],
    )

    _add_tracked_activity_dates(store._con)
    got = store.get_tracked_activity(aid)
    assert got["start_date"] == "2026-07-13"
    assert got["end_date"] == "2026-07-17"  # fabricated Mon-Fri assumption

    # Idempotent: re-run must not clobber an observed end_date.
    store.set_activity_dates(aid, start_date="2026-07-13", end_date="2026-07-18")
    _add_tracked_activity_dates(store._con)
    assert store.get_tracked_activity(aid)["end_date"] == "2026-07-18"


# ── the single date write path + invariants ──────────────────────────


def test_week_block_derives_week_start_and_default_end(store):
    aid = store.track_activity("u1", name="Camp Galileo", start_date="2026-07-13")
    got = store.get_tracked_activity(aid)
    # Plan invariant: week_block => week_start == start_date.
    assert got["week_start"] == got["start_date"] == "2026-07-13"
    assert got["end_date"] == "2026-07-17"
    assert got["rrule"] is None


def test_legacy_week_start_converges_into_the_date_model(store):
    aid = store.track_activity("u1", name="Old Caller Camp", week_start="2026-08-03")
    got = store.get_tracked_activity(aid)
    assert got["start_date"] == "2026-08-03"
    assert got["week_start"] == "2026-08-03"


def test_recurring_weekly_stores_rrule_and_derives_appointment(store):
    aid = store.track_activity(
        "u1", name="Soccer Practice", kid_name="Mar",
        activity_type="extracurricular",
        rrule="FREQ=WEEKLY;BYDAY=TU", recur_time="16:00", recur_duration_min=60,
        start_date="2026-09-01", end_date="2026-12-15",
    )
    got = store.get_tracked_activity(aid)
    # Plan invariant: recurring_weekly => rrule NOT NULL; not a week-block item.
    assert got["rrule"] == "FREQ=WEEKLY;BYDAY=TU"
    assert got["week_start"] is None

    derived = [r for r in store.list_recurring_appointments("u1")
               if r.get("activity_id") == aid]
    assert len(derived) == 1
    assert derived[0]["weekday"] == 1  # TU
    assert derived[0]["start_time"] == "16:00"
    assert derived[0]["end_time"] == "17:00"
    assert derived[0]["title"] == "Soccer Practice"


def test_rrule_change_regenerates_not_duplicates(store):
    aid = store.track_activity(
        "u1", name="Practice", rrule="FREQ=WEEKLY;BYDAY=TU", recur_time="16:00",
    )
    # "Practice moved to Thursdays" — edit the ACTIVITY; derivation reconciles.
    store.set_activity_dates(aid, rrule="FREQ=WEEKLY;BYDAY=TH", recur_time="15:30")
    derived = [r for r in store.list_recurring_appointments("u1")
               if r.get("activity_id") == aid]
    assert len(derived) == 1
    assert derived[0]["weekday"] == 3  # TH
    assert derived[0]["start_time"] == "15:30"


def test_switch_recurring_to_week_block_clears_derived_row(store):
    aid = store.track_activity(
        "u1", name="Was Recurring", rrule="FREQ=WEEKLY;BYDAY=MO", recur_time="09:00",
    )
    store.set_activity_dates(aid, start_date="2026-07-20")
    got = store.get_tracked_activity(aid)
    assert got["rrule"] is None
    assert got["week_start"] == "2026-07-20"
    assert [r for r in store.list_recurring_appointments("u1")
            if r.get("activity_id") == aid] == []


def test_delete_cascades_derived_recurring_row(store):
    aid = store.track_activity(
        "u1", name="Doomed", rrule="FREQ=WEEKLY;BYDAY=FR", recur_time="10:00",
    )
    store.delete_tracked_activity(aid)
    assert [r for r in store.list_recurring_appointments("u1")
            if r.get("activity_id") == aid] == []


def test_update_tracked_activity_refuses_direct_date_writes(store):
    aid = store.track_activity("u1", name="Camp", start_date="2026-07-13")
    # Date fields are silently dropped by the generic patch path — the ONE
    # write path is set_activity_dates (callers route there explicitly).
    store.update_tracked_activity(aid, week_start="2026-08-31", notes="hi")
    got = store.get_tracked_activity(aid)
    assert got["week_start"] == "2026-07-13"
    assert got["notes"] == "hi"


# ── weekly-only RRULE validation (edges) ─────────────────────────────


def test_weekly_rrule_validation():
    assert verticals.weekly_rrule_error(None) is None
    assert verticals.weekly_rrule_error("FREQ=WEEKLY;BYDAY=TU") is None
    assert verticals.weekly_rrule_error(
        "FREQ=WEEKLY;BYDAY=TU;UNTIL=20261215") is None
    assert verticals.weekly_rrule_error("FREQ=DAILY") is not None
    assert verticals.weekly_rrule_error("FREQ=MONTHLY;BYDAY=TU") is not None
    assert verticals.weekly_rrule_error("FREQ=WEEKLY") is not None
    assert verticals.weekly_rrule_error("FREQ=WEEKLY;BYDAY=TU,TH") is not None
    assert verticals.weekly_rrule_error("garbage") is not None


# ── format_when: the one server-side date renderer ───────────────────


def test_format_when_week_block():
    assert lifecycle.format_when(
        {"week_start": "2026-07-13"}) == "Week of Jul 13"
    assert lifecycle.format_when(
        {"start_date": "2026-08-03"}) == "Week of Aug 3"
    assert lifecycle.format_when({}) is None


def test_format_when_recurring():
    assert lifecycle.format_when({
        "rrule": "FREQ=WEEKLY;BYDAY=TU", "recur_time": "16:00",
        "end_date": "2026-12-15",
    }) == "Tuesdays 4:00 PM through Dec 15"
    assert lifecycle.format_when({
        "rrule": "FREQ=WEEKLY;BYDAY=SA",
    }) == "Saturdays"


def test_board_payload_carries_when(store):
    aid = store.track_activity("u1", name="Camp", start_date="2026-07-13")
    board = lifecycle.build_board(
        [store.get_tracked_activity(aid)], [], gmail_connected=False
    )
    cards = [a for s in board["stages"] for a in s["activities"]]
    assert cards[0]["when"] == "Week of Jul 13"


# ── coverage: capability for linked entries, kind-set fallback else ──


def _entries():
    return [
        # Unlinked manual camp week (pre-Phase-2 world) — kind-set fallback.
        {"kid_name": "Ceiba", "week_start": "2026-07-13", "kind": "camp",
         "activity_id": None, "source": "manual"},
        # External gcal pull, covering kind, no link — fallback must hold.
        {"kid_name": "Ceiba", "week_start": "2026-07-20", "kind": "class",
         "activity_id": None, "source": "gcal"},
        # Linked to a tracked OUTING — vertical says outings are NOT coverage.
        {"kid_name": "Ceiba", "week_start": "2026-07-27", "kind": "event",
         "activity_id": "act-outing", "source": "cos_agent"},
        # Linked to a tracked CAMP — vertical says coverage.
        {"kid_name": "Ceiba", "week_start": "2026-08-03", "kind": "camp",
         "activity_id": "act-camp", "source": "cos_agent"},
    ]


_WEEKS = ["2026-07-13", "2026-07-20", "2026-07-27", "2026-08-03"]
_KIDS = [{"name": "Ceiba"}]


def test_uncovered_weeks_without_tracked_matches_legacy_behavior():
    # Before/after snapshot, legacy half: with no tracked list, every entry
    # falls back to the original kind-set rule — gap list unchanged.
    gaps = planning.uncovered_weeks(_entries(), _WEEKS, _KIDS)
    assert [g["week_start"] for g in gaps] == ["2026-07-27"]  # kind=event


def test_uncovered_weeks_linked_entries_decide_by_vertical():
    tracked = [
        {"id": "act-outing", "activity_type": "outing"},
        {"id": "act-camp", "activity_type": "camp"},
    ]
    gaps = planning.uncovered_weeks(_entries(), _WEEKS, _KIDS, tracked)
    # The linked outing still isn't coverage; the unlinked + gcal weeks and
    # the linked camp week stay covered — identical gap list to legacy.
    assert [g["week_start"] for g in gaps] == ["2026-07-27"]


def test_uncovered_weeks_linked_camp_kind_mismatch_still_covers():
    # A linked camp whose calendar kind is 'event' (mis-kinded row): the
    # VERTICAL decides for linked entries, so it covers anyway.
    entries = [{"kid_name": "Ceiba", "week_start": "2026-07-13",
                "kind": "event", "activity_id": "act-camp"}]
    tracked = [{"id": "act-camp", "activity_type": "camp"}]
    assert planning.uncovered_weeks(entries, ["2026-07-13"], _KIDS, tracked) == []
    # ...and without the tracked join it would have been a gap (fallback).
    assert planning.uncovered_weeks(entries, ["2026-07-13"], _KIDS) != []
