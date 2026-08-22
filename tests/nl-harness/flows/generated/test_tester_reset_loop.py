# flows/generated/test_tester_reset_loop.py
#
# @generated_from: specs/tier-2/tester-reset-loop.flow.yml
# @generated_at: 2026-08-21T00:00:00Z
# @modules: admin, profile, cos, auth
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.personas.new_parent import new_parent as _make_new_parent  # noqa: E402

pytestmark = [
    pytest.mark.tier2,
    pytest.mark.requires_admin_token,
]


def _seed(flow_ctx, parent, *, parent_name: str, kid: str) -> None:
    resp = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent_name,
            "kids": [{"name": kid, "age": "7", "temperament": "", "pronouns": "", "grade_band": ""}],
            "parent_week_tasks": ["An errand to fit in"],
        },
        as_=parent,
    )
    assert resp.status_code == 200, f"seed failed: {resp.status_code}: {resp.text[:300]}"


def _board_card_count(flow_ctx, parent) -> int:
    resp = flow_ctx.get("/cos/plan/board", as_=parent)
    assert resp.status_code == 200, resp.text
    return sum(len(stage["activities"]) for stage in resp.json()["stages"])


def _children(flow_ctx, parent) -> dict:
    resp = flow_ctx.get("/profile", as_=parent)
    assert resp.status_code == 200, resp.text
    return resp.json().get("children") or {}


def test_reset_gate_and_unknown_user(flow_ctx, admin, new_parent):
    # Anonymous → 401 (never a silent wipe).
    resp = flow_ctx.post(f"/admin/users/{new_parent.user_id}/reset")
    assert resp.status_code == 401, (
        f"reset without admin token must 401, got {resp.status_code}: {resp.text[:200]}"
    )
    # Unknown user → 404.
    resp = flow_ctx.post(
        "/admin/users/nl-harness-does-not-exist-000/reset", as_=admin,
    )
    assert resp.status_code == 404, (
        f"reset of unknown user must 404, got {resp.status_code}: {resp.text[:200]}"
    )


def test_reset_keeps_identity_and_reonboard_loop(flow_ctx, admin, new_parent):
    tester = new_parent
    bystander = _make_new_parent(flow_ctx)

    _seed(flow_ctx, tester, parent_name="Greg", kid="Lily")
    _seed(flow_ctx, bystander, parent_name="Heather", kid="Maisey")
    assert "Lily" in _children(flow_ctx, tester)
    assert _board_card_count(flow_ctx, tester) >= 1
    bystander_cards_before = _board_card_count(flow_ctx, bystander)

    # ── The reset ────────────────────────────────────────────────────
    resp = flow_ctx.post(f"/admin/users/{tester.user_id}/reset", as_=admin)
    assert resp.status_code == 200, f"reset failed: {resp.status_code}: {resp.text[:300]}"
    body = resp.json()
    assert body.get("ok") is True and body.get("user_id") == tester.user_id
    assert body.get("identity_kept") is True, f"identity_kept missing/false: {body}"
    counts = body.get("counts")
    assert isinstance(counts, dict) and counts, f"per-table counts missing: {body}"

    # ── Family data is gone, credential is not ───────────────────────
    # The same bearer still authenticates (identity kept) …
    prof = flow_ctx.get("/profile", as_=tester)
    assert prof.status_code == 200, (
        f"tester's token must still authenticate after reset, got {prof.status_code}"
    )
    # … but the family is empty.
    assert not (prof.json().get("children") or {}), (
        f"children survived reset: {prof.json().get('children')!r}"
    )
    assert _board_card_count(flow_ctx, tester) == 0, "board cards survived reset"

    # ── Bystander untouched ──────────────────────────────────────────
    assert "Maisey" in _children(flow_ctx, bystander), "bystander children affected"
    assert _board_card_count(flow_ctx, bystander) == bystander_cards_before, (
        "bystander board affected by another user's reset"
    )

    # ── The re-onboard loop ──────────────────────────────────────────
    _seed(flow_ctx, tester, parent_name="Greg", kid="Benjamin")
    kids_after = _children(flow_ctx, tester)
    assert "Benjamin" in kids_after, f"re-seed after reset failed: {kids_after!r}"
    assert "Lily" not in kids_after, (
        f"pre-reset kid resurrected after re-seed: {kids_after!r}"
    )
    assert _board_card_count(flow_ctx, tester) >= 1, "re-seeded board is empty"
