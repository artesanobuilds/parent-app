"""
Phase 0 of the vertical expansion: `tracked_activities.activity_type` exists
end-to-end. Covers the v16 migration backfill (idempotent, everything -> camp),
the write-time derivation rules in `track_activity` (explicit type wins ->
candidate category decides -> camp default), NULL/unknown degradation, and the
board payload contract (`build_board` cards always carry a canonical
activity_type). Hermetic — tempfile DuckDB, no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cos import lifecycle, verticals  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.migrations import _add_tracked_activity_type  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "phase0.duckdb")


# ── taxonomy helpers ─────────────────────────────────────────────────


def test_normalize_degrades_unknown_and_null_to_camp():
    assert verticals.normalize_activity_type(None) == "camp"
    assert verticals.normalize_activity_type("") == "camp"
    assert verticals.normalize_activity_type("soccer!!") == "camp"
    assert verticals.normalize_activity_type("  Trip ") == "trip"
    for t in verticals.ACTIVITY_TYPES:
        assert verticals.normalize_activity_type(t) == t


def test_derive_from_category_maps_candidate_vocab():
    assert verticals.derive_from_category("camp") == "camp"
    assert verticals.derive_from_category("art camp") == "camp"
    assert verticals.derive_from_category("class") == "extracurricular"
    assert verticals.derive_from_category("program") == "extracurricular"
    assert verticals.derive_from_category("weekend") == "outing"
    assert verticals.derive_from_category("event") == "outing"
    assert verticals.derive_from_category(None) == "camp"
    assert verticals.derive_from_category("mystery") == "camp"


# ── v16 migration backfill ───────────────────────────────────────────


def test_v16_backfill_is_camp_and_idempotent(store):
    aid = store.track_activity("u1", name="Legacy Row")
    # Simulate a pre-v16 row: NULL out the type the insert path set.
    store._con.execute(
        "UPDATE tracked_activities SET activity_type = NULL WHERE id = ?", [aid]
    )

    _add_tracked_activity_type(store._con)
    got = store.get_tracked_activity(aid)
    assert got["activity_type"] == "camp"

    # Idempotent: re-run must not error and must not clobber a typed row.
    store.update_tracked_activity(aid, activity_type="trip")
    _add_tracked_activity_type(store._con)
    assert store.get_tracked_activity(aid)["activity_type"] == "trip"


# ── write-time derivation rules ──────────────────────────────────────


def _insert_candidate(store, candidate_id: str, category: str) -> None:
    store._con.execute(
        "INSERT INTO activity_candidates (id, run_id, user_id, name, category) "
        "VALUES (?, 'run1', 'u1', 'Cand', ?)",
        [candidate_id, category],
    )


def test_candidate_category_decides_when_type_omitted(store):
    _insert_candidate(store, "cand-class", "class")
    aid = store.track_activity("u1", name="Fall Pottery", candidate_id="cand-class")
    assert store.get_tracked_activity(aid)["activity_type"] == "extracurricular"


def test_explicit_type_wins_over_candidate(store):
    _insert_candidate(store, "cand-class2", "class")
    aid = store.track_activity(
        "u1", name="Sleepaway", candidate_id="cand-class2", activity_type="camp"
    )
    assert store.get_tracked_activity(aid)["activity_type"] == "camp"


def test_unknown_explicit_type_falls_back_to_candidate(store):
    _insert_candidate(store, "cand-weekend", "weekend")
    aid = store.track_activity(
        "u1", name="Saturday Thing", candidate_id="cand-weekend",
        activity_type="not-a-vertical",
    )
    assert store.get_tracked_activity(aid)["activity_type"] == "outing"


def test_no_candidate_no_type_defaults_camp(store):
    aid = store.track_activity("u1", name="Manual Add")
    assert store.get_tracked_activity(aid)["activity_type"] == "camp"


def test_patch_can_retype(store):
    aid = store.track_activity("u1", name="Was A Camp")
    store.update_tracked_activity(aid, activity_type="extracurricular")
    assert store.get_tracked_activity(aid)["activity_type"] == "extracurricular"


# ── board payload contract ───────────────────────────────────────────


def test_build_board_cards_carry_canonical_activity_type(store):
    store.track_activity("u1", name="Typed", activity_type="extracurricular")
    legacy = store.track_activity("u1", name="Legacy")
    store._con.execute(
        "UPDATE tracked_activities SET activity_type = NULL WHERE id = ?", [legacy]
    )

    acts = store.list_tracked_activities("u1")
    board = lifecycle.build_board(acts, todos=[])
    cards = [a for s in board["stages"] for a in s["activities"]]
    assert len(cards) == 2
    types = {c["name"]: c["activity_type"] for c in cards}
    assert types["Typed"] == "extracurricular"
    assert types["Legacy"] == "camp"  # NULL degrades, never leaks to clients


# ── lifecycle.transition: the one status write path ──────────────────


def test_transition_into_watched_seeds_payment_todo(store):
    aid = store.track_activity("u1", name="Robotics", price_amount=250.0)
    updated = lifecycle.transition(store, "u1", aid, "signed_up")
    assert updated["status"] == "signed_up"
    todos = [t for t in store.list_todos("u1") if t.get("activity_id") == aid]
    assert any(t["kind"] == "payment" for t in todos)


def test_transition_into_declined_dismisses_open_todos(store):
    aid = store.track_activity("u1", name="Chess Club", price_amount=100.0)
    lifecycle.transition(store, "u1", aid, "signed_up")
    updated = lifecycle.transition(store, "u1", aid, "declined")
    assert updated["status"] == "declined"
    open_todos = [
        t for t in store.list_todos("u1", status="open")
        if t.get("activity_id") == aid
    ]
    assert open_todos == []


def test_transition_carries_extra_fields_in_same_write(store):
    aid = store.track_activity("u1", name="Sailing")
    updated = lifecycle.transition(
        store, "u1", aid, "planned",
        extra_fields={"decision_rationale": "closest to home"},
    )
    assert updated["status"] == "planned"
    assert updated["decision_rationale"] == "closest to home"


def test_transition_unknown_id_returns_none(store):
    assert lifecycle.transition(store, "u1", "nope", "planned") is None


def test_on_created_fires_only_for_watched_status(store):
    a1 = store.track_activity("u1", name="Direct Save", status="signed_up",
                              price_amount=90.0)
    lifecycle.on_created(store, "u1", a1, "signed_up")
    assert any(
        t["kind"] == "payment"
        for t in store.list_todos("u1") if t.get("activity_id") == a1
    )
    a2 = store.track_activity("u1", name="Just Considering", price_amount=90.0)
    lifecycle.on_created(store, "u1", a2, "exploring")
    assert [t for t in store.list_todos("u1") if t.get("activity_id") == a2] == []
