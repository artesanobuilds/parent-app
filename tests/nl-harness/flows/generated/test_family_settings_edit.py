# flows/generated/test_family_settings_edit.py
#
# @generated_from: specs/tier-1/family-settings-edit.flow.yml
# @generated_at: 2026-08-09T00:00:00Z
# @modules: profile
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_family_settings_language_and_coach_style_round_trip(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")

    parent = existing_parent

    # ── GET /profile returns the parent's current fields ────────────
    before = flow_ctx.get("/profile", as_=parent)
    assert before.status_code == 200, before.text
    assert "parent" in before.json()

    # ── PATCH secondary_language + guidance_style, both echoed back ──
    patched = flow_ctx.patch(
        "/profile",
        json={"secondary_language": "es", "guidance_style": "concise scripts"},
        as_=parent,
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["parent"]["secondary_language"] == "es", body
    assert body["parent"]["guidance_style"] == "concise scripts", body

    # ── A follow-up GET reflects the same two values ─────────────────
    after = flow_ctx.get("/profile", as_=parent)
    assert after.status_code == 200, after.text
    fresh_parent = after.json()["parent"]
    assert fresh_parent["secondary_language"] == "es"
    assert fresh_parent["guidance_style"] == "concise scripts"

    # ── PATCHing an unrelated field leaves the two settings alone ────
    unrelated = flow_ctx.patch("/profile", json={"name": "Bilingual Household"}, as_=parent)
    assert unrelated.status_code == 200, unrelated.text
    assert unrelated.json()["parent"]["guidance_style"] == "concise scripts", \
        "an unrelated PATCH must not reset guidance_style"

    # ── GET /household/members succeeds (the roster the circle/ ─────
    # care-giver cards read) ──────────────────────────────────────────
    members = flow_ctx.get("/household/members", as_=parent)
    assert members.status_code == 200, members.text
    assert "members" in members.json()


def test_family_settings_patch_requires_auth(flow_ctx):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")
    anon = flow_ctx.patch("/profile", json={"secondary_language": "es"})
    assert anon.status_code == 401, f"unauthenticated PATCH /profile must 401; got {anon.status_code}"
