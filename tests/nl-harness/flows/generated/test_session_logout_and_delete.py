# flows/generated/test_session_logout_and_delete.py
#
# @generated_from: specs/tier-1/session-logout-and-delete.flow.yml
# @generated_at: 2026-07-18T23:30:00Z
# @modules: auth, profile, legal
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_logout_then_self_serve_delete(flow_ctx, new_parent):
    parent = new_parent

    # ── give the family something to lose ───────────────────────────
    seed = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent.display_name,
            "kids": [{"name": "DeleteMeKid", "age": "7"}],
        },
        as_=parent,
    )
    assert seed.status_code == 200, seed.text
    status = flow_ctx.get("/legal/status", as_=parent).json()
    versions = {d["slug"]: d["required_version"] for d in status["documents"]}
    if versions:
        assert flow_ctx.post(
            "/legal/accept", json={"versions": versions}, as_=parent
        ).status_code == 200

    # ── log out: empty body = revoke-all; must be safe for legacy
    #    sessions that have no refresh token to revoke ────────────────
    out = flow_ctx.post("/auth/logout", json={}, as_=parent)
    assert out.status_code == 200, out.text
    assert out.json().get("ok") is True
    # Legacy opaque bearers aren't refresh lineages — the CLIENT discards
    # them on sign-out. The server-side revocation contract for v1 refresh
    # tokens is locked in mvp-backend/tests/test_auth_v2.py.
    assert flow_ctx.get("/profile", as_=parent).status_code == 200

    # ── self-serve delete: the Settings → Delete account promise ────
    deleted = flow_ctx.delete(f"/family/{parent.user_id}", as_=parent)
    assert deleted.status_code == 200, deleted.text
    body = deleted.json()
    assert body.get("ok") is True
    assert isinstance(body.get("deleted"), dict) and body["deleted"], body

    # ── nothing of the family is served anymore ─────────────────────
    reissued = flow_ctx.post("/auth/issue-token", json={"user_id": parent.user_id})
    assert reissued.status_code == 200, reissued.text
    parent.token = reissued.json()["token"]

    profile = flow_ctx.get("/profile", as_=parent).json()
    assert not (profile.get("parent") or {}).get("name"), profile
    assert not profile.get("children"), profile
    if versions:
        fresh = flow_ctx.get("/legal/status", as_=parent).json()
        assert fresh["accepted_all"] is False, "legal acceptances survived the delete"

    # ── idempotent: deleting again is safe (fixture cleanup relies on it) ─
    assert flow_ctx.delete(f"/family/{parent.user_id}", as_=parent).status_code == 200
