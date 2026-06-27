"""
Reliability: `claim_next_queued_run` is exactly-once under thread contention.
Many worker threads racing to claim the same queue must each get distinct runs —
no run claimed twice (would double-process / double-charge), no run dropped. This
is what makes the multi-worker pool safe; the atomic `UPDATE … RETURNING` under
the storage RLock is the guarantee.

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
    return DuckDBStorage(db_path=tmp_path / "rel_claim.duckdb")


def test_claim_is_exactly_once_under_contention(store):
    M = 25           # queued runs
    THREADS = 8      # racing claimers

    queued_ids = {
        store.create_research_run(user_id=f"u{i % 5}", location={}, kids=[])
        for i in range(M)
    }
    assert len(queued_ids) == M

    claimed: list[str] = []
    claimed_lock = threading.Lock()
    start = threading.Event()

    def claimer():
        start.wait(timeout=5)  # release all threads at once → maximize the race
        while True:
            run = store.claim_next_queued_run()
            if run is None:
                break
            with claimed_lock:
                claimed.append(run["id"])

    threads = [threading.Thread(target=claimer) for _ in range(THREADS)]
    for t in threads:
        t.start()
    start.set()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive(), "a claimer thread hung"

    # Exactly-once: every queued run claimed, none twice, none lost.
    assert len(claimed) == M, f"expected {M} claims, got {len(claimed)}"
    assert len(set(claimed)) == M, "a run was claimed by more than one worker"
    assert set(claimed) == queued_ids, "claimed set != queued set (a run was dropped)"

    # And the queue is genuinely drained.
    assert store.claim_next_queued_run() is None
