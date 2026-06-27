# flows/generated/test_research_openai_outage.py
#
# @generated_from: specs/tier-2/research-openai-outage.flow.yml
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


def test_openai_outage_fails_run_gracefully(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.fault.available:
        pytest.skip("fault injection unavailable; run via tools/run-fault-flows.sh")

    parent = new_parent
    flow_ctx.register_cleanup("reset openai fault", lambda: flow_ctx.fault.reset())

    # Hard outage: every model call 503s until reset. Retries exhaust, the worker
    # catches, and the run must end FAILED — not hang, and not cascade a 5xx to
    # the client. This is the contract that a dead dependency degrades gracefully.
    flow_ctx.fault("openai", "down")

    resp = flow_ctx.post("/research/runs", json={"user_id": parent.user_id}, as_=parent)
    # The enqueue API itself stays healthy even though the dependency is down.
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]

    def is_failed() -> bool:
        s = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
        # The poll endpoint must keep answering 200 throughout — no cascade.
        assert s.status_code == 200, f"poll endpoint returned {s.status_code} during outage"
        return s.json().get("status") == "failed"

    flow_ctx.wait_for(
        is_failed, timeout_s=60, interval_s=1.5,
        description="research run fails gracefully under an OpenAI outage",
    )

    body = flow_ctx.get(f"/research/runs/{run_id}", as_=parent).json()
    assert body.get("error"), f"a failed run should carry an error message: {body}"
