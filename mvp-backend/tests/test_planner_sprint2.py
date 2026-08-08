"""Tests for beta-v1 sprint-2 planner redesign backend changes.

Migration v22: fit_score + fit_reason survive tracking.
Activity-vs-activity overlap detection.
All to-dos (open + completed) in the board payload.
"""
from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pytest


def _fresh_db() -> str:
    """A private on-disk DB per test.

    NOT ``":memory:"`` — that path returns a process-wide shared connection in
    this codebase (see debugging_inmemory_singleton_delete), so tests using it
    accumulate each other's rows and assertions like ``len(activities) == 1``
    fail with 3. Each test gets its own temp file instead.
    """
    return str(Path(tempfile.mkdtemp()) / "planner.duckdb")


def test_migration_v22_adds_fit_fields():
    """Migration v22 adds fit_score + fit_reason to tracked_activities and
    fit_reason to activity_candidates. Idempotent on re-run."""
    from app.duckdb_storage import DuckDBStorage
    from app.migrations import _add_tracked_activity_fit_fields

    storage = DuckDBStorage(db_path=_fresh_db())
    con = storage._con

    # Run the migration
    _add_tracked_activity_fit_fields(con)

    # Verify tracked_activities has the new columns
    tracked_cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tracked_activities'"
        ).fetchall()
    }
    assert "fit_score" in tracked_cols
    assert "fit_reason" in tracked_cols

    # Verify activity_candidates has fit_reason
    cand_cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'activity_candidates'"
        ).fetchall()
    }
    assert "fit_reason" in cand_cols

    # Re-run should be idempotent
    _add_tracked_activity_fit_fields(con)

    # Columns should still exist
    tracked_cols_after = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tracked_activities'"
        ).fetchall()
    }
    assert "fit_score" in tracked_cols_after
    assert "fit_reason" in tracked_cols_after
    storage.close()


def test_migration_v22_on_existing_db():
    """Migration v22 works against a DB stamped at v21 with existing rows."""
    from app.duckdb_storage import DuckDBStorage
    from app.migrations import _add_tracked_activity_fit_fields

    storage = DuckDBStorage(db_path=_fresh_db())
    con = storage._con
    user_id = "user-migration-test"

    # Create a tracked activity without fit fields (simulating v21 schema)
    activity_id = storage.track_activity(
        user_id, name="Summer Camp", kid_name="Test Kid",
        status="exploring"
    )

    # Run the migration
    _add_tracked_activity_fit_fields(con)

    # Verify the existing row is intact
    activity = storage.get_tracked_activity(activity_id)
    assert activity is not None
    assert activity["name"] == "Summer Camp"
    assert activity["kid_name"] == "Test Kid"
    # New fields should be NULL for existing rows
    assert activity.get("fit_score") is None
    assert activity.get("fit_reason") is None

    # New rows should be able to use the fields
    activity_id_2 = storage.track_activity(
        user_id, name="Art Class", kid_name="Test Kid",
        status="exploring", fit_score=0.85, fit_reason="Matches age and interest in art"
    )
    activity_2 = storage.get_tracked_activity(activity_id_2)
    assert activity_2["fit_score"] == 0.85
    assert activity_2["fit_reason"] == "Matches age and interest in art"
    storage.close()


def test_fit_score_and_reason_survive_tracking():
    """fit_score and fit_reason are copied from candidate to tracked_activity."""
    from app.duckdb_storage import DuckDBStorage

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-fit-test"
    run_id = "run-fit-test"

    # Insert a candidate with fit_score and fit_reason
    storage.insert_activity_candidates(
        run_id=run_id,
        user_id=user_id,
        candidates=[
            {
                "name": "Soccer Camp",
                "kid_name": "Ben",
                "category": "camp",
                "fit_score": 0.75,
                "fit_reason": "Weekly drop-in fits flexible schedule and age 7-12",
                "provider": "YMCA",
                "city": "Gig Harbor",
            }
        ]
    )

    candidates = storage.list_candidates(run_id=run_id)
    assert len(candidates) == 1
    candidate_id = candidates[0]["id"]
    assert candidates[0]["fit_score"] == 0.75
    assert candidates[0]["fit_reason"] == "Weekly drop-in fits flexible schedule and age 7-12"

    # Track the candidate
    activity_id = storage.track_activity(
        user_id,
        name="Soccer Camp",
        kid_name="Ben",
        candidate_id=candidate_id,
        status="exploring"
    )

    # Verify fit_score and fit_reason were copied forward
    activity = storage.get_tracked_activity(activity_id)
    assert activity["fit_score"] == 0.75
    assert activity["fit_reason"] == "Weekly drop-in fits flexible schedule and age 7-12"
    storage.close()


def test_activity_overlap_detection():
    """detect_time_conflicts flags overlapping date ranges for the same kid."""
    from app.duckdb_storage import DuckDBStorage
    from app.cos import planning

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-overlap-test"

    # Create two overlapping activities for the same kid
    camp_id = storage.track_activity(
        user_id,
        name="Summer Camp",
        kid_name="Lily",
        start_date="2026-06-22",
        end_date="2026-08-28",
        status="planned"
    )

    trip_id = storage.track_activity(
        user_id,
        name="Rialto Beach trip",
        kid_name="Lily",
        start_date="2026-08-15",
        end_date="2026-08-17",
        status="planned"
    )

    # Create a non-overlapping activity
    storage.track_activity(
        user_id,
        name="Fall Soccer",
        kid_name="Lily",
        start_date="2026-09-01",
        end_date="2026-09-30",
        status="planned"
    )

    activities = storage.list_tracked_activities(user_id)

    # Detect conflicts
    conflicts = planning.detect_time_conflicts(
        calendar_entries=[],
        recurring=[],
        tracked_activities=activities
    )

    # Should find one overlap: camp vs trip
    overlap_conflicts = [c for c in conflicts if c.get("type") == "activity_overlap"]
    assert len(overlap_conflicts) == 1

    conflict = overlap_conflicts[0]
    assert conflict["kid_name"] == "Lily"
    assert set([conflict["activity_a_name"], conflict["activity_b_name"]]) == {
        "Summer Camp", "Rialto Beach trip"
    }
    assert conflict["overlap_start"] == "2026-08-15"
    assert conflict["overlap_end"] == "2026-08-17"
    assert "overlaps" in conflict["detail"].lower()
    storage.close()


def test_declined_activities_dont_conflict():
    """Declined activities are excluded from overlap warnings."""
    from app.duckdb_storage import DuckDBStorage
    from app.cos import planning

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-declined-test"

    # Create two overlapping activities, one declined
    storage.track_activity(
        user_id,
        name="Camp A",
        kid_name="Ben",
        start_date="2026-07-01",
        end_date="2026-07-15",
        status="declined"
    )

    storage.track_activity(
        user_id,
        name="Camp B",
        kid_name="Ben",
        start_date="2026-07-10",
        end_date="2026-07-20",
        status="planned"
    )

    activities = storage.list_tracked_activities(user_id)

    conflicts = planning.detect_time_conflicts(
        calendar_entries=[],
        recurring=[],
        tracked_activities=activities
    )

    # Should find no overlap because one is declined
    overlap_conflicts = [c for c in conflicts if c.get("type") == "activity_overlap"]
    assert len(overlap_conflicts) == 0
    storage.close()


def test_completed_todos_in_board_payload():
    """Board payload includes completed to-dos alongside open ones."""
    from app.duckdb_storage import DuckDBStorage
    from app.cos import lifecycle

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-todos-test"

    # Create an activity
    activity_id = storage.track_activity(
        user_id,
        name="Soccer Camp",
        kid_name="Lily",
        status="planned"
    )

    # Add open and completed to-dos
    storage.add_todo(
        user_id,
        activity_id=activity_id,
        title="Register Ben",
        status="done"
    )

    storage.add_todo(
        user_id,
        activity_id=activity_id,
        title="Register Lily",
        status="done"
    )

    storage.add_todo(
        user_id,
        activity_id=activity_id,
        title="Forward confirmation email",
        status="open"
    )

    activities = storage.list_tracked_activities(user_id)
    todos = storage.list_todos(user_id)

    board = lifecycle.build_board(activities, todos)

    # Find the activity in the board
    all_activities = []
    for stage in board["stages"]:
        all_activities.extend(stage["activities"])

    activity_entry = next(a for a in all_activities if a["id"] == activity_id)

    # Should have 1 open to-do
    assert len(activity_entry["open_todos"]) == 1
    assert activity_entry["open_todos"][0]["title"] == "Forward confirmation email"

    # Should have 3 total to-dos (open + completed)
    assert len(activity_entry["all_todos"]) == 3
    titles = {t["title"] for t in activity_entry["all_todos"]}
    assert titles == {
        "Register Ben",
        "Register Lily",
        "Forward confirmation email"
    }

    # Verify status
    done_todos = [t for t in activity_entry["all_todos"] if t["status"] == "done"]
    assert len(done_todos) == 2
    storage.close()


def test_fit_fields_exposed_in_payloads():
    """fit_score and fit_reason appear in activity list and board payloads."""
    from app.duckdb_storage import DuckDBStorage
    from app.cos import lifecycle

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-payload-test"

    activity_id = storage.track_activity(
        user_id,
        name="Art Camp",
        kid_name="Lily",
        fit_score=0.82,
        fit_reason="Age 7-12, art interest, close to home",
        status="exploring"
    )

    # Check GET /activities payload
    activities = storage.list_tracked_activities(user_id)
    assert len(activities) == 1
    assert activities[0]["fit_score"] == 0.82
    assert activities[0]["fit_reason"] == "Age 7-12, art interest, close to home"

    # Check board payload
    board = lifecycle.build_board(activities, [])
    all_activities = []
    for stage in board["stages"]:
        all_activities.extend(stage["activities"])

    activity_entry = next(a for a in all_activities if a["id"] == activity_id)
    assert activity_entry["fit_score"] == 0.82
    assert activity_entry["fit_reason"] == "Age 7-12, art interest, close to home"
    storage.close()


# Note: Each test creates its own in-memory database for isolation


def test_board_payload_matches_the_ios_contract():
    """Cross-surface lock for the sprint-2 planner card.

    The backend and iOS were built in parallel and drifted: the backend emitted
    `all_todos` and put overlaps in a flat `conflicts` list, while
    `PlanService.swift` decoded `todos` and a per-activity `overlaps: [{activity_id,
    name, range}]`. Nothing failed loudly — iOS Codable just yields nil and the
    "Still to do" checklist and overlap warning render EMPTY, which looks like a
    design choice rather than a bug.

    This asserts the exact keys `BoardActivity`/`PlanTodo`/`ActivityOverlap`
    declare, in the same spirit as test_onboarding_seed_contract.
    """
    from app.duckdb_storage import DuckDBStorage
    from app.cos import lifecycle, planning

    storage = DuckDBStorage(db_path=_fresh_db())
    user_id = "user-contract"

    a_id = storage.track_activity(
        user_id, name="YMCA Day Camp", kid_name="Lily", status="signed_up",
        start_date="2026-06-22", end_date="2026-08-28",
        fit_score=0.75, fit_reason="Closest full-day option to home.",
    )
    b_id = storage.track_activity(
        user_id, name="Rialto Beach trip", kid_name="Lily", status="planned",
        start_date="2026-08-15", end_date="2026-08-17",
    )
    done_id = storage.add_todo(user_id, title="Register Lily", activity_id=a_id)
    storage.update_todo(done_id, status="done")
    storage.add_todo(user_id, title="Forward the confirmation email", activity_id=a_id)

    activities = storage.list_tracked_activities(user_id)
    conflicts = planning.detect_time_conflicts([], [], tracked_activities=activities)
    board = lifecycle.build_board(
        activities, storage.list_todos(user_id), conflicts=conflicts,
    )

    card = None
    for stage in board["stages"]:
        for entry in stage["activities"]:
            if entry["id"] == a_id:
                card = entry
    assert card is not None, "the tracked activity is missing from every stage"

    # BoardActivity's sprint-2 keys.
    assert card["fit_score"] == 0.75
    assert card["fit_reason"] == "Closest full-day option to home."

    # PlanTodo decodes `todos` (open AND completed) with a `done` projection.
    labels = {t["title"]: t["done"] for t in card["todos"]}
    assert labels == {"Register Lily": True, "Forward the confirmation email": False}, labels
    # open_todos keeps its narrower meaning — next_step and the follow-ups list
    # depend on it being open-only.
    assert [t["title"] for t in card["open_todos"]] == ["Forward the confirmation email"]

    # ActivityOverlap: exactly {activity_id, name, range}, pointing at the OTHER
    # activity, with the range pre-rendered server-side (the format_when rule).
    assert len(card["overlaps"]) == 1
    ov = card["overlaps"][0]
    assert set(ov) == {"activity_id", "name", "range"}
    assert ov["activity_id"] == b_id
    assert ov["name"] == "Rialto Beach trip"
    assert ov["range"] == "Aug 15–17", ov["range"]

    # And the reciprocal side sees it too.
    other = None
    for stage in board["stages"]:
        for entry in stage["activities"]:
            if entry["id"] == b_id:
                other = entry
    assert other and other["overlaps"][0]["activity_id"] == a_id
