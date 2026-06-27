"""
Unit tests for the background research worker (app/research/worker.py).

Hermetic: a tempfile DuckDBStorage + an injected fake discovery function, so no
LLM / network / deepagents calls. Verifies the run lifecycle (claim -> done),
candidate persistence, and the failure path (discover raises -> run 'failed').
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.research.worker import ResearchWorker, init_worker  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "worker.duckdb")


def _fake_discover(**kwargs):
    # Echoes a couple of candidates; also proves the worker passes location/kids.
    assert "location" in kwargs and "kids" in kwargs
    return [
        {"name": "Camp Tule", "kid_name": "Ceiba", "category": "camp", "fit_score": 0.8},
        {"name": "Little Monsters", "kid_name": "Ceiba", "category": "camp", "fit_score": 0.6},
    ]


def test_worker_processes_run_to_done(store):
    run_id = store.create_research_run(
        user_id="u1", location={"postal_code": "95448"}, kids=[{"name": "Ceiba", "age": 8}],
    )
    worker = ResearchWorker(store, _fake_discover)

    claimed = store.claim_next_queued_run()
    assert claimed["id"] == run_id
    worker.process_run(claimed)

    run = store.get_research_run(run_id)
    assert run["status"] == "done"
    assert run["candidate_count"] == 2
    assert run["progress"]["phase"] == "done"
    assert run["finished_at"] is not None

    cands = store.list_candidates(run_id=run_id)
    assert {c["name"] for c in cands} == {"Camp Tule", "Little Monsters"}
    assert cands[0]["name"] == "Camp Tule"  # ranked by fit_score desc


def test_worker_marks_run_failed_on_discover_error(store):
    run_id = store.create_research_run(user_id="u1", location={}, kids=[])
    worker = ResearchWorker(store, lambda **kw: (_ for _ in ()).throw(RuntimeError("tavily exploded")))

    claimed = store.claim_next_queued_run()
    worker.process_run(claimed)

    run = store.get_research_run(run_id)
    assert run["status"] == "failed"
    assert "tavily exploded" in (run["error"] or "")
    assert run["finished_at"] is not None
    assert store.list_candidates(run_id=run_id) == []


def test_init_worker_sets_singleton(store):
    import app.research.worker as worker_mod

    w = init_worker(store, discover_fn=_fake_discover)
    assert worker_mod.research_worker is w


def test_thread_pool_drains_concurrently(store):
    """N queued runs are processed by N worker threads in parallel — the total
    wall-clock is ~1 slow run, not N serial runs (the head-of-line-blocking fix).
    Each fake discover blocks on a barrier so they MUST overlap to finish."""
    import threading
    import time

    N = 3
    barrier = threading.Barrier(N, timeout=5)
    run_ids = [
        store.create_research_run(user_id=f"u{i}", location={}, kids=[]) for i in range(N)
    ]

    def _blocking_discover(**kwargs):
        # Won't return until all N are running at once — proves real concurrency.
        barrier.wait()
        return [{"name": "Camp", "category": "camp"}]

    worker = ResearchWorker(store, _blocking_discover, poll_interval=0.2, concurrency=N)
    worker.start()
    try:
        deadline = time.time() + 8
        while time.time() < deadline:
            if all(store.get_research_run(r)["status"] == "done" for r in run_ids):
                break
            time.sleep(0.1)
    finally:
        worker.stop(timeout=2)

    statuses = [store.get_research_run(r)["status"] for r in run_ids]
    assert statuses == ["done"] * N, statuses  # barrier would deadlock if serial


def test_create_run_dedupes_active(store):
    """A second create while one is in flight returns the SAME run (no pile-up)."""
    first = store.create_research_run(user_id="u1", location={}, kids=[])
    active = store.get_active_research_run("u1")
    assert active is not None and active["id"] == first and active["status"] == "queued"

    # Once it's terminal, a new create is NOT deduped (active returns None).
    store.update_research_run(first, status="done", candidate_count=0, finished=True)
    assert store.get_active_research_run("u1") is None
