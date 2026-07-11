# flows/generated/test_cross_family_isolation.py
#
# @generated_from: specs/tier-1/cross-family-isolation.flow.yml
# @generated_at: 2026-07-07T00:00:00Z
# @modules: auth, cos, research, kid_agent
# @promoted_by: (none -- awaiting review)
#
import pytest

from lib.personas.existing_parent import existing_parent as _make_existing_parent

pytestmark = pytest.mark.tier1


def test_family_b_cannot_touch_family_a_rows(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")

    # Two unrelated families. The `existing_parent` fixture is cached per-test,
    # so mint the second family via the factory directly to get a distinct id.
    family_a = existing_parent
    family_b = _make_existing_parent(flow_ctx)
    assert family_a.user_id != family_b.user_id, "personas must be distinct families"

    # ── Family A tracks an activity it owns ─────────────────────────
    created = flow_ctx.post(
        "/cos/activities/track",
        json={"user_id": family_a.user_id, "name": "Family A Soccer", "status": "interested"},
        as_=family_a,
    )
    assert created.status_code == 200, created.text
    activity_id = created.json()["id"]

    # Family A can read it back.
    listed_a = flow_ctx.get("/cos/activities", as_=family_a).json()["activities"]
    assert any(a["id"] == activity_id for a in listed_a)

    # ── Family B PATCH → 404 (no existence oracle) + no mutation ────
    patched = flow_ctx.patch(
        f"/cos/activities/{activity_id}",
        json={"user_id": family_b.user_id, "status": "confirmed"},
        as_=family_b,
    )
    assert patched.status_code == 404, \
        f"cross-family PATCH must 404 (not 403/200); got {patched.status_code}"

    # ── Family B DELETE → 404 + no delete ───────────────────────────
    deleted = flow_ctx.delete(f"/cos/activities/{activity_id}", as_=family_b)
    assert deleted.status_code == 404, \
        f"cross-family DELETE must 404; got {deleted.status_code}"

    # ── Family A's activity survived untouched ──────────────────────
    still = flow_ctx.get("/cos/activities", as_=family_a).json()["activities"]
    match = [a for a in still if a["id"] == activity_id]
    assert match, "Family A's activity was deleted by a cross-family request!"
    assert match[0]["status"] == "interested", \
        "Family A's activity was mutated by a cross-family PATCH!"


def test_family_b_cannot_read_family_a_research_run(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")

    family_a = existing_parent
    family_b = _make_existing_parent(flow_ctx)
    assert family_a.user_id != family_b.user_id

    run = flow_ctx.post("/research/runs", json={"user_id": family_a.user_id}, as_=family_a)
    assert run.status_code == 200, run.text
    run_id = run.json().get("id") or run.json().get("run_id")
    assert run_id, f"no run id in response: {run.json()}"

    cross = flow_ctx.get(f"/research/runs/{run_id}", as_=family_b)
    assert cross.status_code == 404, \
        f"Family B reading Family A's run must 404; got {cross.status_code}"
