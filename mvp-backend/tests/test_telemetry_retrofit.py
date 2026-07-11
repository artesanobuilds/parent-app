"""Phase 3.9 (vertical expansion): telemetry retrofit.

Locks the counter facade's no-op/swallow-safe posture, the strict-allowlist
registration of the new product events, and the load-bearing call sites:
lifecycle transitions emit both channels, hook failures COUNT (they're
swallow-safe by design, so the counter is the only machine-readable signal),
and taxonomy degradation counts only for non-NULL escapees.
Hermetic — no OTel exporter, no PostHog, tempfile DuckDB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.observability as observability  # noqa: E402
from app.analytics.events import EVENTS  # noqa: E402
from app.cos import lifecycle, verticals  # noqa: E402
from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "telemetry.duckdb")


@pytest.fixture()
def counted(monkeypatch):
    """Record every observability.count() call (module-attr patch reaches all
    call sites, which import the module object, not the function)."""
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        observability, "count",
        lambda name, n=1, **labels: calls.append((name, labels)),
    )
    return calls


# ── The facade ───────────────────────────────────────────────────────


def test_count_is_noop_and_swallow_safe_when_otel_off():
    # OTel is off in tests: must not raise, must not create counters.
    observability.count("cos.test.metric", to_stage="x")
    assert observability._counters == {}


# ── Allowlist registration ───────────────────────────────────────────


def test_new_events_and_props_registered():
    assert {"status", "activity_type", "date_model"} <= EVENTS["activity_tracked"]
    assert EVENTS["activity_stage_advanced"] == {"to_stage", "activity_type"}
    assert EVENTS["door_opened"] == {"door"}
    assert EVENTS["door_converted"] == {"door"}


# ── Lifecycle transitions emit both channels ─────────────────────────


def test_transition_counts_and_captures(store, counted, monkeypatch):
    captured: list[tuple[str, str, dict]] = []
    import app.analytics as analytics
    monkeypatch.setattr(
        analytics, "capture",
        lambda event, user_id, props=None: captured.append((event, user_id, props)),
    )

    aid = store.track_activity(
        "u1", name="Fall Soccer", activity_type="extracurricular",
        rrule="FREQ=WEEKLY;BYDAY=TU", recur_time="16:00",
    )
    counted.clear()  # drop the cos.dates.write from the insert
    lifecycle.transition(store, "u1", aid, "planned")

    transitions = [c for c in counted if c[0] == "cos.lifecycle.transition"]
    assert transitions == [
        ("cos.lifecycle.transition",
         {"to_stage": "to_register", "activity_type": "extracurricular"}),
    ]
    events = [c for c in captured if c[0] == "activity_stage_advanced"]
    assert events == [
        ("activity_stage_advanced", "u1",
         {"to_stage": "to_register", "activity_type": "extracurricular"}),
    ]


def test_status_group_covers_every_status():
    expected = {
        "exploring": "considering", "interested": "considering",
        "reference": "considering", "planned": "to_register",
        "signed_up": "registered", "confirmed": "registered",
        "done": "done", "pending_eligibility": "blocked",
        "waitlisted": "blocked", "declined": "declined",
        "garbage": "considering", None: "considering",
    }
    for status, group in expected.items():
        assert lifecycle._status_group(status) == group, status


# ── Hook failures are counted (the swallow-safe paths' only signal) ──


def test_hook_error_counter_fires(store, counted):
    aid = store.track_activity("u1", name="Camp X", price_amount=100.0)
    activity = store.get_tracked_activity(aid)

    class BoomTodos:
        def __getattr__(self, name):
            if name == "list_todos":
                raise RuntimeError("db exploded")
            return getattr(store, name)

    lifecycle.on_enter_watched(BoomTodos(), "u1", activity)  # must not raise
    assert ("cos.lifecycle.hook_error", {"hook": "on_enter_watched"}) in counted


# ── Taxonomy degradation counts non-NULL escapees only ───────────────


def test_type_degradation_counting(counted):
    verticals.get_profile(None)
    verticals.get_profile("")
    verticals.get_profile("camp")
    verticals.get_profile("  OUTING ")
    assert counted == []  # NULLs + registered types never count

    expected = ["cos.type.degraded"]
    verticals.get_profile("garbage")
    # Canonical-but-unregistered types also count (set shrinks phase by phase).
    pending = sorted(verticals.ACTIVITY_TYPES - set(verticals.REGISTRY))
    for key in pending:
        verticals.get_profile(key)
        expected.append("cos.type.degraded")
    assert [c[0] for c in counted] == expected
