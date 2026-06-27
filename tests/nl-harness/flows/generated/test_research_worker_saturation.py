# flows/generated/test_research_worker_saturation.py
#
# @generated_from: specs/tier-2/research-worker-saturation.flow.yml
# @generated_at: 2026-06-27T00:00:00Z
# @modules: research, reliability, fault-injection
# @promoted_by: (none -- awaiting review)
#
import concurrent.futures
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.personas import new_parent as make_parent  # noqa: E402

pytestmark = [pytest.mark.tier2, pytest.mark.requires_openai]

N = 5  # > RESEARCH_WORKER_CONCURRENCY default (3), so the queue path is exercised


def test_pool_drains_under_saturation(flow_ctx):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.fault.available:
        pytest.skip("fault injection unavailable; run via tools/run-fault-flows.sh")

    # Healthy mock: each run completes in one fast canned model call, so this is
    # the deterministic, free analog of the offline concurrency test — the whole
    # pipeline (enqueue → pool drain → completion) under saturation.
    flow_ctx.fault.reset()

    parents = [make_parent(flow_ctx) for _ in range(N)]

    def start(parent):
        resp = flow_ctx.post("/research/runs", json={"user_id": parent.user_id}, as_=parent)
        return parent, resp

    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as pool:
        results = list(pool.map(start, parents))

    runs = []
    for parent, resp in results:
        assert resp.status_code == 200, f"{parent.user_id}: {resp.status_code} {resp.text}"
        runs.append((parent, resp.json()["run_id"]))

    def all_done() -> bool:
        for parent, run_id in runs:
            s = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
            if s.status_code != 200 or s.json().get("status") != "done":
                return False
        return True

    def any_failed() -> bool:
        for parent, run_id in runs:
            s = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
            if s.status_code == 200 and s.json().get("status") == "failed":
                return True
        return False

    # Every run drains to done — none stranded queued, none lost. With the old
    # single-threaded worker this still completes, but the pool makes it parallel;
    # the value here is proving N>pool all reach a terminal success under load.
    flow_ctx.wait_for(
        all_done, timeout_s=60, interval_s=1.0, fail_if=any_failed,
        description=f"all {N} saturated runs drain to done",
    )
