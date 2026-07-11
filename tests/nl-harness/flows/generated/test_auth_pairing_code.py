# flows/generated/test_auth_pairing_code.py
#
# @generated_from: specs/tier-1/auth-pairing-code.flow.yml
# @generated_at: 2026-07-08T00:00:00Z
# @modules: auth
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_pairing_code_phone_to_dashboard(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")

    parent = existing_parent

    # ── Unauthenticated mint is rejected ────────────────────────────
    anon = flow_ctx.post("/auth/pairing-code")
    assert anon.status_code == 401, \
        f"unauthenticated pairing-code must 401; got {anon.status_code}"

    # ── Authenticated parent mints a short code ─────────────────────
    made = flow_ctx.post("/auth/pairing-code", as_=parent)
    assert made.status_code == 200, made.text
    body = made.json()
    assert "code" in body and "expires_in" in body, f"missing fields: {body}"
    code = body["code"]

    # ── Dashboard redeems it for a v1 session (same user_id) ────────
    session = flow_ctx.post("/auth/pairing-login", json={"code": code})
    assert session.status_code == 200, session.text
    s = session.json()
    for key in ("access_token", "refresh_token", "user_id"):
        assert key in s, f"session missing {key!r}: {s}"
    assert s["user_id"] == parent.user_id, \
        "pairing session bound to a different user_id than the minting parent"
    assert s["access_token"].count(".") == 2, "access_token is not a JWT"

    # ── The access token authenticates a protected endpoint ─────────
    prof = flow_ctx.get(
        "/profile",
        params={"user_id": parent.user_id},
        as_=_Bearer(s["access_token"]),
    )
    assert prof.status_code == 200, \
        f"paired access token should authenticate /profile; got {prof.status_code}"

    # ── Single use: a second redeem of the same code fails ──────────
    reuse = flow_ctx.post("/auth/pairing-login", json={"code": code})
    assert reuse.status_code == 401, \
        f"pairing code must be single-use; second redeem got {reuse.status_code}"


def test_pairing_login_rejects_bogus_code(flow_ctx):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")
    bad = flow_ctx.post("/auth/pairing-login", json={"code": "NOPE-NOPE"})
    assert bad.status_code == 401, f"bogus pairing code must 401; got {bad.status_code}"


class _Bearer:
    """Minimal persona shim: carries a bearer token for flow_ctx auth dispatch
    (the harness reads `.token` off the persona)."""
    def __init__(self, token: str) -> None:
        self.token = token
