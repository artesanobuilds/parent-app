# flows/generated/test_research_backoff_recovery.py
#
# @generated_from: specs/tier-2/research-backoff-recovery.flow.yml
# @generated_at: 2026-06-27T00:00:00Z
# @modules: research, reliability, fault-injection
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = [pytest.mark.tier2, pytest.mark.requires_openai]


def test_run_survives_transient_429(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.fault.available:
        pytest.skip("fault injection unavailable; run via tools/run-fault-flows.sh")

    parent = new_parent
    # Always heal the mock at teardown, even if an assertion fails.
    flow_ctx.register_cleanup("reset openai fault", lambda: flow_ctx.fault.reset())

    # The next 2 model calls 429, then the mock self-heals. Without backoff the
    # first 429 would fail the run; with it the run rides through to completion.
    flow_ctx.fault("openai", "rate_limit", count=2)

    resp = flow_ctx.post("/research/runs", json={"user_id": parent.user_id}, as_=parent)
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]
    flow_ctx.register_cleanup(
        f"cancel run {run_id}",
        lambda: flow_ctx.post(f"/research/runs/{run_id}/cancel", as_=parent),
    )

    def is_done() -> bool:
        s = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
        return s.status_code == 200 and s.json().get("status") == "done"

    def is_failed() -> bool:
        s = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
        return s.status_code == 200 and s.json().get("status") == "failed"

    # Reaches done DESPITE the 429s — fail fast if it instead errors out.
    flow_ctx.wait_for(
        is_done, timeout_s=45, interval_s=1.0, fail_if=is_failed,
        description="research run completes despite transient 429s",
    )

    # The mock actually served the 429s — proves the retry path was exercised,
    # not that the faults were silently skipped.
    state = flow_ctx.fault.state()
    assert state["fault_count"] >= 2, f"expected >=2 injected 429s, got {state}"
