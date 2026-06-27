"""
Reliability: crash recovery. A restart kills in-flight worker threads, leaving
runs stuck `running`. The startup sweeper (`requeue_stale_running_runs`) must
re-queue exactly those, and leave terminal runs (done/failed/canceled) untouched,
so the run completes after the restart instead of silently stranding.

Hermetic: tempfile DuckDB, no LLM.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "rel_sweep.duckdb")


def test_sweeper_requeues_running_only(store):
    # Three runs; drive them to distinct states.
    r_running = store.create_research_run(user_id="u", location={}, kids=[])
    r_done = store.create_research_run(user_id="u", location={}, kids=[])
    r_queued = store.create_research_run(user_id="u", location={}, kids=[])

    # Claim the oldest (r_running) → running. Mark the second done. Leave the third queued.
    claimed = store.claim_next_queued_run()
    assert claimed["id"] == r_running
    store.update_research_run(r_done, status="done", candidate_count=0, finished=True)

    # Simulate a restart sweep.
    n = store.requeue_stale_running_runs()

    assert n == 1, f"expected 1 requeue, got {n}"
    assert store.get_research_run(r_running)["status"] == "queued"  # rescued
    assert store.get_research_run(r_done)["status"] == "done"       # left alone
    assert store.get_research_run(r_queued)["status"] == "queued"   # untouched

    # The rescued run is claimable again (so it actually completes post-restart).
    again = store.claim_next_queued_run()
    assert again["id"] in {r_running, r_queued}


def test_sweeper_is_noop_when_nothing_running(store):
    store.create_research_run(user_id="u", location={}, kids=[])  # queued only
    assert store.requeue_stale_running_runs() == 0
