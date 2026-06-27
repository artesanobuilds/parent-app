"""
Reliability: the research worker thread pool drains the queue *in parallel*,
bounded by `concurrency` — the fix for the June-24 head-of-line-blocking incident
(a single-threaded worker serialized concurrent parents → minutes of "0 found").

Hermetic: tempfile DuckDB + an injected discover_fn that parks on an event so we
can observe how many runs execute at once. No LLM / network.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.research.worker import ResearchWorker  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "rel_conc.duckdb")


def _done_count(store, user_id="u", n_users=1):
    total = 0
    for i in range(n_users):
        total += sum(
            1 for r in store.list_research_runs(f"{user_id}{i}", limit=100)
            if r["status"] == "done"
        )
    return total


def test_pool_runs_in_parallel_bounded_by_concurrency(store):
    POOL = 3
    N = 6  # twice the pool, so the back half must wait for a free slot

    lock = threading.Lock()
    active = 0
    max_active = 0
    started = threading.Semaphore(0)
    release = threading.Event()

    def discover(**kwargs):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        started.release()
        release.wait(timeout=5)  # hold the slot so overlap is observable
        with lock:
            active -= 1
        return [{"name": "Camp", "category": "camp"}]

    for i in range(N):
        store.create_research_run(user_id=f"u{i}", location={}, kids=[])

    worker = ResearchWorker(store, discover, poll_interval=0.2, concurrency=POOL)
    worker.start()
    try:
        # Exactly POOL runs should be in-flight at once — not 1 (serial), not N.
        for _ in range(POOL):
            assert started.acquire(timeout=5), "pool never reached full occupancy"
        time.sleep(0.3)  # give any (incorrect) extra worker a chance to start
        with lock:
            assert active == POOL, f"expected {POOL} concurrent runs, saw {active}"
            assert max_active == POOL, f"pool exceeded its bound: {max_active}"

        # Release the first wave → the back half claims the freed slots → all done.
        release.set()
        deadline = time.time() + 8
        while time.time() < deadline:
            if all(
                store.list_research_runs(f"u{i}", limit=1)[0]["status"] == "done"
                for i in range(N)
            ):
                break
            time.sleep(0.1)
        statuses = [store.list_research_runs(f"u{i}", limit=1)[0]["status"] for i in range(N)]
        assert statuses == ["done"] * N, statuses
    finally:
        release.set()
        worker.stop(timeout=2)
