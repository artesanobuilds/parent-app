"""
Unit tests for the activity-planning research storage layer (duckdb_storage.py):
run lifecycle (queue -> claim -> update -> finish), the startup re-queue sweeper,
and idempotent candidate insert + ranked listing. Hermetic — a tempfile DuckDB,
no network.
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
    return DuckDBStorage(db_path=tmp_path / "research.duckdb")


def test_run_lifecycle_queue_claim_finish(store):
    run_id = store.create_research_run(
        user_id="u1",
        location={"postal_code": "95448", "country": "US"},
        kids=[{"name": "Ceiba", "age": 8}],
        params={"max_queries": 12},
    )
    run = store.get_research_run(run_id)
    assert run["status"] == "queued"
    assert run["location"]["postal_code"] == "95448"
    assert run["kids"][0]["name"] == "Ceiba"

    claimed = store.claim_next_queued_run()
    assert claimed is not None and claimed["id"] == run_id
    assert claimed["status"] == "running"

    # No more queued runs to claim.
    assert store.claim_next_queued_run() is None

    store.update_research_run(run_id, progress={"phase": "search", "queries_done": 3})
    assert store.get_research_run(run_id)["progress"]["queries_done"] == 3

    store.update_research_run(run_id, status="done", candidate_count=5, finished=True)
    done = store.get_research_run(run_id)
    assert done["status"] == "done"
    assert done["candidate_count"] == 5
    assert done["finished_at"] is not None


def test_enqueue_dedupe_retargets_queued_run_params(store):
    """The 'select 50 → get 25' bug: a second enqueue must NOT silently drop the
    new params. A still-queued run gets RETARGETED to the new request."""
    first = store.enqueue_research_run(
        user_id="u1", location={"postal_code": "95448"}, kids=[],
        params={"max_candidates": 25},
    )
    assert first["deduped"] is False
    # Re-pick 50 and re-submit while the run is still queued.
    second = store.enqueue_research_run(
        user_id="u1", location={"postal_code": "95448"}, kids=[],
        params={"max_candidates": 50, "radius_miles": 50},
    )
    assert second["deduped"] is True
    assert second["run_id"] == first["run_id"]  # same run reused …
    run = store.get_research_run(first["run_id"])
    assert run["params"]["max_candidates"] == 50   # … but retargeted to the new params
    assert run["params"]["radius_miles"] == 50


def test_enqueue_dedupe_running_run_is_not_retargeted(store):
    """A run already RUNNING can't be retargeted mid-flight — it dedupes as-is."""
    first = store.enqueue_research_run(
        user_id="u2", location={}, kids=[], params={"max_candidates": 25},
    )
    store.claim_next_queued_run()  # flip it to running
    second = store.enqueue_research_run(
        user_id="u2", location={}, kids=[], params={"max_candidates": 50},
    )
    assert second["deduped"] is True
    assert store.get_research_run(first["run_id"])["params"]["max_candidates"] == 25


def test_requeue_stale_running_runs(store):
    run_id = store.create_research_run(
        user_id="u1", location={"postal_code": "1"}, kids=[],
    )
    store.claim_next_queued_run()  # -> running
    assert store.get_research_run(run_id)["status"] == "running"

    n = store.requeue_stale_running_runs()
    assert n == 1
    assert store.get_research_run(run_id)["status"] == "queued"


def test_insert_candidates_is_idempotent_per_run(store):
    run_id = store.create_research_run(
        user_id="u1", location={"postal_code": "1"}, kids=[],
    )
    batch = [
        {"name": "Camp Tule", "kid_name": "Ceiba", "category": "camp", "fit_score": 0.7},
        {"name": "Little Monsters", "kid_name": "Ceiba", "category": "camp", "fit_score": 0.9,
         "contact": {"name": "Carey", "email": "carey@example.com"}},
    ]
    assert store.insert_activity_candidates(run_id=run_id, user_id="u1", candidates=batch) == 2

    # Re-running the same run replaces, not appends (idempotent recovery).
    assert store.insert_activity_candidates(run_id=run_id, user_id="u1", candidates=batch) == 2
    rows = store.list_candidates(run_id=run_id)
    assert len(rows) == 2

    # Ranked by fit_score desc; JSON contact round-trips.
    assert rows[0]["name"] == "Little Monsters"
    assert rows[0]["contact"]["name"] == "Carey"

    # Filtering works.
    assert len(store.list_candidates(user_id="u1", category="camp")) == 2
    assert store.list_candidates(user_id="u1", kid_name="Nobody") == []


def test_list_research_runs_newest_first(store):
    a = store.create_research_run(user_id="u1", location={}, kids=[])
    b = store.create_research_run(user_id="u1", location={}, kids=[])
    runs = store.list_research_runs("u1")
    assert [r["id"] for r in runs][:2] == [b, a]
    # Scoped to the user.
    assert store.list_research_runs("someone-else") == []
