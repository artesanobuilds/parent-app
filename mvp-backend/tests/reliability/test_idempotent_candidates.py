"""
Reliability: re-running a research run REPLACES its candidates, never appends.
The sweeper re-queues stale `running` runs, so a run can execute more than once;
`insert_activity_candidates` must be delete-then-insert or a crash-recovered run
would double its candidate list.

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
    return DuckDBStorage(db_path=tmp_path / "rel_idem.duckdb")


def test_rerun_replaces_candidates_no_duplication(store):
    run_id = store.create_research_run(user_id="u", location={}, kids=[])
    batch = [
        {"name": "Camp Tule", "category": "camp", "fit_score": 0.8},
        {"name": "Little Monsters", "category": "camp", "fit_score": 0.6},
    ]

    n1 = store.insert_activity_candidates(run_id=run_id, user_id="u", candidates=batch)
    n2 = store.insert_activity_candidates(run_id=run_id, user_id="u", candidates=batch)  # re-run

    assert n1 == 2 and n2 == 2
    listed = store.list_candidates(run_id=run_id)
    assert len(listed) == 2, f"re-run duplicated candidates: {len(listed)} rows"
    assert {c["name"] for c in listed} == {"Camp Tule", "Little Monsters"}


def test_rerun_with_fewer_candidates_shrinks(store):
    run_id = store.create_research_run(user_id="u", location={}, kids=[])
    store.insert_activity_candidates(
        run_id=run_id, user_id="u",
        candidates=[{"name": f"C{i}", "category": "camp"} for i in range(5)],
    )
    # A second pass finds fewer — the list reflects the latest run, not the union.
    store.insert_activity_candidates(
        run_id=run_id, user_id="u",
        candidates=[{"name": "C0", "category": "camp"}],
    )
    assert len(store.list_candidates(run_id=run_id)) == 1
