# flows/generated/test_admin_token_gating.py
#
# @generated_from: specs/tier-1/admin-token-gating.flow.yml
# @generated_at: 2026-05-31T15:00:00Z
# @modules: cms, data_export
# @promoted_by: (none -- awaiting review)
#
from dataclasses import dataclass

import pytest

pytestmark = [
    pytest.mark.tier1,
    pytest.mark.requires_admin_token,
]


@dataclass
class _BogusAdmin:
    """Sentinel: looks like an admin persona but with a wrong token. Used to
    verify the gate rejects invalid values (not just absence)."""
    admin_token: str = "this-is-not-the-real-admin-token-987654"


def test_data_export_admin_gate(flow_ctx, admin):
    # ── Anonymous: gate refuses ─────────────────────────────────────
    anon_resp = flow_ctx.get("/data/export")
    assert anon_resp.status_code == 401, (
        f"/data/export should require admin token; got {anon_resp.status_code}: "
        f"{anon_resp.text[:200]}"
    )

    # ── Wrong token: gate refuses ───────────────────────────────────
    wrong_resp = flow_ctx.get("/data/export", as_=_BogusAdmin())
    assert wrong_resp.status_code == 401, (
        f"/data/export with bogus token should 401; got {wrong_resp.status_code}: "
        f"{wrong_resp.text[:200]}"
    )

    # ── Correct token: gate opens, manifest returned ────────────────
    ok_resp = flow_ctx.get("/data/export", as_=admin)
    assert ok_resp.status_code == 200, ok_resp.text
    body = ok_resp.json()
    assert "checksums" in body, f"expected `checksums` in manifest, got {list(body.keys())}"
    assert isinstance(body["checksums"], dict)


def test_cms_mutation_endpoints_require_admin(flow_ctx, admin):
    # POST /cms/categories without token → 401
    resp = flow_ctx.post(
        "/cms/categories",
        json={"id": "nl-harness-cat", "name": "Harness", "emoji": "*",
              "description": "throwaway"},
    )
    assert resp.status_code == 401, (
        f"/cms/categories without admin token should 401; got {resp.status_code}: "
        f"{resp.text[:200]}"
    )

    # POST /cms/export-parquet without token → 401
    resp = flow_ctx.post("/cms/export-parquet")
    assert resp.status_code == 401, (
        f"/cms/export-parquet without admin token should 401; got {resp.status_code}"
    )


def test_public_content_endpoints_unaffected_by_admin_token(flow_ctx):
    """Sanity check: gating /cms/* and /data/* did not accidentally gate /content/*."""
    resp = flow_ctx.get("/content/categories")
    assert resp.status_code == 200, \
        "anon read of /content/categories should still work; gating regression?"
