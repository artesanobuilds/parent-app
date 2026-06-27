"""
Reliability: run dedup. `get_active_research_run` (used by `POST /research/runs`)
matches only an in-flight run (queued or running) for *that* user, so a double-tap
reuses the run instead of stacking another behind it in the worker queue. A
terminal run must NOT dedup (the next search should start fresh), and one user's
in-flight run must never mask another's.

Hermetic: tempfile DuckDB, no LLM.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "rel_dedup.duckdb")


def test_active_run_matches_queued_and_running_not_terminal(store):
    run_id = store.create_research_run(user_id="u", location={}, kids=[])

    # queued → active
    active = store.get_active_research_run("u")
    assert active is not None and active["id"] == run_id and active["status"] == "queued"

    # running → still active (dedup must hold while the worker is mid-run)
    store.claim_next_queued_run()
    active = store.get_active_research_run("u")
    assert active is not None and active["id"] == run_id and active["status"] == "running"

    # terminal → NOT active (a new search should create a fresh run)
    store.update_research_run(run_id, status="done", candidate_count=0, finished=True)
    assert store.get_active_research_run("u") is None


@pytest.mark.parametrize("terminal", ["done", "failed", "canceled"])
def test_terminal_states_do_not_dedup(store, terminal):
    run_id = store.create_research_run(user_id="u", location={}, kids=[])
    store.update_research_run(run_id, status=terminal, finished=True)
    assert store.get_active_research_run("u") is None


def test_dedup_is_per_user(store):
    a = store.create_research_run(user_id="alice", location={}, kids=[])
    store.create_research_run(user_id="bob", location={}, kids=[])

    # alice's in-flight run must not leak into bob's dedup and vice-versa.
    assert store.get_active_research_run("alice")["id"] == a
    assert store.get_active_research_run("bob")["id"] != a
    assert store.get_active_research_run("carol") is None


def test_atomic_enqueue_same_user_creates_exactly_one(store):
    """The dedupe-or-create TOCTOU guard: many submits firing for the SAME user
    at once must yield exactly ONE run — one creator, the rest deduped. Without
    the transaction wrap, several would slip past the check and create duplicates
    (wasted LLM/Tavily spend)."""
    T = 12
    results: list[dict] = []
    rlock = threading.Lock()
    start = threading.Event()

    def submit():
        start.wait(timeout=5)  # release all at once → maximize the race window
        r = store.enqueue_research_run(user_id="u", location={}, kids=[])
        with rlock:
            results.append(r)

    threads = [threading.Thread(target=submit) for _ in range(T)]
    for t in threads:
        t.start()
    start.set()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive()

    runs = store.list_research_runs("u", limit=50)
    assert len(runs) == 1, f"TOCTOU: {len(runs)} runs created for one user, expected 1"
    assert len({r["run_id"] for r in results}) == 1, "submitters resolved to different runs"
    creators = [r for r in results if not r["deduped"]]
    assert len(creators) == 1, f"expected exactly 1 creator, got {len(creators)}"
    assert len(results) == T  # everyone got an answer
