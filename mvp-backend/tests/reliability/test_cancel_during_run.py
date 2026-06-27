"""
Reliability: a run cancelled WHILE the worker is executing it must stay
cancelled — the worker must not resurrect it to `done` (or `failed`) when its
work finishes, and must not leave candidates under a cancelled run.

Found by the load+chaos hunt (tools/load_and_chaos.py, E2): cancel returned
`canceled`, then the finishing worker clobbered it back to `done`, so cancel was
ineffective and a terminal state regressed. Fixed via `finalize_run_if_running`
(a conditional terminal write). This locks it down.

Hermetic: tempfile DuckDB + an injected discover_fn that parks on an event.
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
    return DuckDBStorage(db_path=tmp_path / "rel_cancel.duckdb")


def test_cancel_mid_run_is_not_clobbered(store):
    entered = threading.Event()
    release = threading.Event()

    def discover(**kwargs):
        entered.set()
        release.wait(timeout=5)  # hold the run "in flight" so we can cancel it
        return [{"name": "Camp", "category": "camp"}]

    run_id = store.create_research_run(user_id="u", location={}, kids=[])
    worker = ResearchWorker(store, discover, poll_interval=0.1, concurrency=1)
    worker.start()
    try:
        assert entered.wait(timeout=5), "worker never started the run"

        # The parent cancels while it's executing (mirrors POST /research/runs/{id}/cancel).
        store.update_research_run(
            run_id, status="canceled", progress={"phase": "canceled"}, finished=True
        )
        assert store.get_research_run(run_id)["status"] == "canceled"

        # Let discovery finish → the worker attempts to finalize. It must NOT win.
        release.set()
        time.sleep(1.0)

        final = store.get_research_run(run_id)
        assert final["status"] == "canceled", \
            f"cancel was clobbered: run regressed to '{final['status']}'"
        # And no candidates leaked under the cancelled run.
        assert store.list_candidates(run_id=run_id) == [], "candidates left under a cancelled run"
    finally:
        release.set()
        worker.stop(timeout=2)


def test_finalize_run_if_running_only_writes_when_running(store):
    run_id = store.create_research_run(user_id="u", location={}, kids=[])

    # queued → finalize is a no-op (not running yet)
    assert store.finalize_run_if_running(run_id, status="done", candidate_count=3) is False
    assert store.get_research_run(run_id)["status"] == "queued"

    # running → finalize transitions it
    store.claim_next_queued_run()
    assert store.finalize_run_if_running(run_id, status="done", candidate_count=3) is True
    got = store.get_research_run(run_id)
    assert got["status"] == "done" and got["candidate_count"] == 3

    # already terminal → no-op (can't be clobbered)
    assert store.finalize_run_if_running(run_id, status="failed", error="x") is False
    assert store.get_research_run(run_id)["status"] == "done"
