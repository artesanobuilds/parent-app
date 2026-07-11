"""Phase 5: V4 school-life — the deterministic (Stage 2) half.

Extraction itself is live-LLM (tests/goldens/test_ingest_goldens.py, opt-in);
everything after it is pure and locked here: the event_kind→task-chain
templates, materialize()'s school behavior (type resolution, single-date,
provenance snippet, chain dedupe, the exploring/pending-only blast-radius
law), materialize_all()'s cap-and-park, and format_when's single-day render.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.observability as observability  # noqa: E402
from app.cos import lifecycle  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.ingest import taxonomy  # noqa: E402
from app.ingest.extract import (  # noqa: E402
    ExtractedActivity, materialize, materialize_all,
)


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "school.duckdb")


def _artifact(store, user_id="u1"):
    return store.insert_ingest_artifact(
        user_id, source="paste", media_type="text", raw_text="fixture"
    )


# ── taxonomy chains ──────────────────────────────────────────────────

def test_chain_templates_per_kind():
    slip = ExtractedActivity(activity_name="Exploratorium Trip",
                             event_kind="permission_slip", dates=["2026-10-23"])
    assert taxonomy.chain_for(slip) == [
        ("Sign and return the permission slip for Exploratorium Trip", "form", "2026-10-23")
    ]
    fee = ExtractedActivity(activity_name="Music", event_kind="fee", amount_due=45.0,
                            payment_due_date="2026-09-18")
    assert taxonomy.chain_for(fee) == [
        ("Pay the $45 fee for Music", "payment", "2026-09-18")
    ]
    assert taxonomy.chain_for(ExtractedActivity(event_kind="general")) == []
    assert taxonomy.chain_for(ExtractedActivity(event_kind="mystery_kind")) == []
    assert taxonomy.chain_for(ExtractedActivity()) == []


# ── materialize: school behavior ─────────────────────────────────────

def test_event_kind_implies_school_event_and_single_date(store):
    ext = ExtractedActivity(
        activity_name="Picture Day", event_kind="picture_day",
        dates=["2026-10-09"], source_snippet="PICTURE DAY IS Friday, October 9",
    )
    created = materialize(store, "u1", _artifact(store), ext)
    activity = store.get_tracked_activity(created["activity_id"])
    assert activity["activity_type"] == "school_event"
    # single_date: one day, not a fabricated week block.
    assert activity["start_date"] == activity["end_date"] == "2026-10-09"
    assert activity["details"]["source_snippet"].startswith("PICTURE DAY")
    assert activity["details"]["source_artifact_id"]
    # format_when renders the DAY.
    assert lifecycle.format_when(activity) == "Oct 9"


def test_explicit_activity_type_wins_over_kind_heuristics(store):
    ext = ExtractedActivity(activity_name="Soccer", activity_type="extracurricular",
                            category="sports")
    created = materialize(store, "u1", _artifact(store), ext)
    assert store.get_tracked_activity(created["activity_id"])["activity_type"] == "extracurricular"


def test_chain_dedupes_by_todo_kind(store):
    # The extractor already produced the payment via payment_due_date — the
    # fee chain must NOT add a second payment to-do.
    ext = ExtractedActivity(
        activity_name="Music Fee", event_kind="fee",
        amount_due=45.0, payment_due_date="2026-09-18",
    )
    created = materialize(store, "u2", _artifact(store, "u2"), ext)
    todos = [t for t in store.list_todos("u2")
             if t["id"] in created["todo_ids"] and t.get("kind") == "payment"]
    assert len(todos) == 1


def test_provenance_rides_todo_detail(store):
    ext = ExtractedActivity(
        activity_name="Field Trip", event_kind="permission_slip",
        source_snippet="permission slips due Oct 23",
    )
    created = materialize(store, "u3", _artifact(store, "u3"), ext)
    todo = next(t for t in store.list_todos("u3") if t["id"] in created["todo_ids"])
    assert 'From: "permission slips due Oct 23"' in (todo.get("detail") or "")


def test_blast_radius_never_watched(store):
    # Even a welcome-letter-looking school item lands exploring/pending only.
    ext = ExtractedActivity(activity_name="Spirit Week", event_kind="spirit_day",
                            is_welcome_letter=True)
    created = materialize(store, "u4", _artifact(store, "u4"), ext)
    status = store.get_tracked_activity(created["activity_id"])["status"]
    assert status in ("exploring", "pending_eligibility")


# ── materialize_all: cap and park ────────────────────────────────────

def test_materialize_all_caps_and_parks(store, monkeypatch):
    counted = []
    monkeypatch.setattr(observability, "count",
                        lambda name, n=1, **labels: counted.append((name, labels)))
    items = [ExtractedActivity(activity_name=f"Event {i}", event_kind="general")
             for i in range(8)]
    result = materialize_all(store, "u5", _artifact(store, "u5"), items)
    assert len(result["items"]) == 5  # INGEST_MAX_ITEMS_PER_ARTIFACT default
    assert result["parked"] == 3
    assert ("ingest.caps.hit", {"cap": "per_artifact"}) in counted
    made = [i for i in result["items"] if i["created"]["activity_id"]]
    assert len(made) == 5


def test_one_bad_item_does_not_eat_the_rest(store, monkeypatch):
    good = ExtractedActivity(activity_name="Fine Event", event_kind="general")
    bad = ExtractedActivity(activity_name="Kaboom", event_kind="general")

    original = store.track_activity

    def exploding(user_id, **kwargs):
        if kwargs.get("name") == "Kaboom":
            raise RuntimeError("db hiccup")
        return original(user_id, **kwargs)

    monkeypatch.setattr(store, "track_activity", exploding)
    result = materialize_all(store, "u6", _artifact(store, "u6"), [bad, good])
    assert len(result["items"]) == 2
    assert result["items"][0]["created"]["activity_id"] is None
    assert result["items"][1]["created"]["activity_id"] is not None
