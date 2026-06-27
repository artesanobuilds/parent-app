# flows/generated/test_research_dedup.py
#
# @generated_from: specs/tier-2/research-dedup.flow.yml
# @generated_at: 2026-06-27T00:00:00Z
# @modules: research, reliability
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

# Make `lib` importable even when pytest is invoked from a different cwd.
HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = [pytest.mark.tier2, pytest.mark.requires_openai]


def test_rapid_resubmit_dedupes_to_one_run(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; a research run would spend OpenAI tokens")

    parent = new_parent  # /auth/issue-token done by the fixture; registers family cleanup

    def start():
        return flow_ctx.post("/research/runs", json={"user_id": parent.user_id}, as_=parent)

    # ── Step 1: first run is fresh (not deduped) ────────────────────
    r1 = start()
    assert r1.status_code == 200, r1.text
    run1 = r1.json()
    run_id = run1.get("run_id")
    assert run_id, f"first run missing run_id: {run1}"
    assert run1.get("deduped") is not True, f"first run should not be deduped: {run1}"

    # Cancel whatever we created, regardless of how the test ends (LIFO: before
    # the persona's family-delete cleanup).
    flow_ctx.register_cleanup(
        f"cancel research run {run_id}",
        lambda: flow_ctx.post(f"/research/runs/{run_id}/cancel", as_=parent),
    )

    # ── Step 2: immediate re-submit dedupes to the same in-flight run ─
    r2 = start()
    assert r2.status_code == 200, r2.text
    run2 = r2.json()
    assert run2.get("run_id") == run_id, \
        f"expected dedup to {run_id}, got a new run: {run2}"
    assert run2.get("deduped") is True, f"second run should be deduped: {run2}"

    # ── Step 3: the deduped run is still in flight ──────────────────
    assert run2.get("status") in ("queued", "running"), \
        f"deduped run should be in flight, got status={run2.get('status')}"
