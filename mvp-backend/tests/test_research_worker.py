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
