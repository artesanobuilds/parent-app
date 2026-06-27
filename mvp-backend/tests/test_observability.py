"""
Observability (last-mile) tests: the Sentry + OTel init is a true no-op when the
env vars are unset (so local/CI/prod-without-config behave exactly as before), and
the research_run_health aggregate that feeds the Grafana gauges is correct.
Hermetic — tempfile DuckDB, no Sentry/OTel/network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import observability  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "obs.duckdb")


def test_init_is_noop_without_env(monkeypatch):
    for key in ("SENTRY_DSN", "OTEL_EXPORTER_OTLP_ENDPOINT"):
        monkeypatch.delenv(key, raising=False)
    assert observability.init_sentry() is False
    assert observability.init_otel(object()) is False
    # register_domain_metrics is a no-op unless OTel actually initialized
    assert observability.register_domain_metrics(object()) is False


def test_research_run_health_empty(store):
    h = store.research_run_health(window_minutes=60)
    assert h["total"] == 0
    assert h["failed"] == 0
    assert h["in_flight"] == 0
    assert h["failure_rate"] == 0.0
    assert h["max_queue_wait_s"] == 0


def test_research_run_health_counts(store):
    # 1 failed, 1 done, 1 still queued (in-flight)
    r1 = store.create_research_run(user_id="u", location={}, kids=[])
    store.claim_next_queued_run()
    store.finalize_run_if_running(r1, status="failed", error="boom")

    r2 = store.create_research_run(user_id="u", location={}, kids=[])
    store.claim_next_queued_run()
    store.finalize_run_if_running(r2, status="done", candidate_count=3)

    store.create_research_run(user_id="u", location={}, kids=[])  # queued → in_flight

    h = store.research_run_health(window_minutes=60)
    assert h["total"] == 3
    assert h["failed"] == 1
    assert h["in_flight"] == 1
    assert abs(h["failure_rate"] - (1 / 3)) < 0.01
