# flows/generated/test_concurrent_enqueue_resilience.py
#
# @generated_from: specs/tier-2/concurrent-enqueue-resilience.flow.yml
# @generated_at: 2026-06-27T00:00:00Z
# @modules: research, reliability
# @promoted_by: (none -- awaiting review)
#
import concurrent.futures
import sys
from pathlib import Path

import pytest

# Make `lib` importable even when pytest is invoked from a different cwd.
HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.personas import new_parent as make_parent  # noqa: E402

pytestmark = [pytest.mark.tier3, pytest.mark.requires_openai]

N = 4  # > RESEARCH_WORKER_CONCURRENCY default (3), so the queue path is exercised too


def test_concurrent_enqueue_no_corruption(flow_ctx):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; concurrent runs would spend OpenAI tokens")

    # Provision N distinct parents up front (each registers its own family-delete
    # cleanup) so the concurrent section only races the enqueue path.
    parents = [make_parent(flow_ctx) for _ in range(N)]

    def enqueue(parent):
        resp = flow_ctx.post(
            "/research/runs", json={"user_id": parent.user_id}, as_=parent
        )
        return parent, resp

    # Fire all N at once — httpx.Client is safe to share across threads.
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as pool:
        results = list(pool.map(enqueue, parents))

    run_ids = []
    for parent, resp in results:
        assert resp.status_code == 200, \
            f"{parent.user_id}: enqueue returned {resp.status_code}: {resp.text}"
        body = resp.json()
        run_id = body.get("run_id")
        assert run_id, f"{parent.user_id}: response missing run_id: {body}"
        run_ids.append(run_id)
        # Bound spend: cancel each run (LIFO, before family deletes).
        flow_ctx.register_cleanup(
            f"cancel research run {run_id}",
            lambda rid=run_id, p=parent: flow_ctx.post(f"/research/runs/{rid}/cancel", as_=p),
        )

    # Distinct users → distinct runs: no claim collision or row corruption under
    # the concurrent writes.
    assert len(set(run_ids)) == N, f"expected {N} distinct run_ids, got {run_ids}"
