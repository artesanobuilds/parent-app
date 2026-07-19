# flows/generated/test_legal_acceptance_lifecycle.py
#
# @generated_from: specs/tier-1/legal-acceptance-lifecycle.flow.yml
# @generated_at: 2026-07-18T23:30:00Z
# @modules: legal, auth, cms
# @promoted_by: (none -- awaiting review)
#
from uuid import uuid4

import pytest

pytestmark = pytest.mark.tier1

LEGAL_SLUGS = {"privacy-policy", "terms"}


def _status(flow_ctx, parent):
    resp = flow_ctx.get("/legal/status", as_=parent)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_public_legal_docs_serve(flow_ctx):
    resp = flow_ctx.get("/content/legal")
    assert resp.status_code == 200, resp.text
    docs = {d["slug"]: d for d in resp.json()["documents"]}
    assert LEGAL_SLUGS <= set(docs), f"missing legal slugs: {docs.keys()}"
    for slug in LEGAL_SLUGS:
        one = flow_ctx.get(f"/content/legal/{slug}")
        assert one.status_code == 200, one.text
        body = one.json()
        for key in ("slug", "version", "body_md", "effective_date"):
            assert key in body, f"{slug} missing {key!r}"
        assert body["body_md"].strip(), f"{slug} has an empty body"
    assert flow_ctx.get("/content/legal/not-a-doc").status_code == 404


def test_fresh_parent_accepts_current_versions(flow_ctx, new_parent):
    parent = new_parent

    # ── fresh account: both docs pending ────────────────────────────
    status = _status(flow_ctx, parent)
    assert status["accepted_all"] is False
    assert set(status["needs"]) == LEGAL_SLUGS, status["needs"]
    versions = {d["slug"]: d["required_version"] for d in status["documents"]}

    # ── a stale echo must 409 (never record text the user didn't see) ─
    stale = flow_ctx.post(
        "/legal/accept",
        json={"versions": {"terms": "0.0-stale-echo"}},
        as_=parent,
    )
    assert stale.status_code == 409, stale.text
    assert "required" in stale.json()

    # ── accepting the versions actually shown lands clean ───────────
    accept = flow_ctx.post(
        "/legal/accept",
        json={"versions": versions, "platform": "harness"},
        as_=parent,
    )
    assert accept.status_code == 200, accept.text
    assert len(accept.json()["accepted"]) == len(versions)
    after = _status(flow_ctx, parent)
    assert after["accepted_all"] is True, after


@pytest.mark.requires_admin_token
def test_publish_reacceptance_cycle(flow_ctx, new_parent, admin):
    """Admin publishes terms vNext with requires_reacceptance → exactly that
    slug re-prompts → parent re-accepts → clean. Cleanup re-publishes the
    prior body (append-only history means no rollback — restore by publish)."""
    parent = new_parent

    # The admin fixture only proves the backend HAS a token (503 probe); a
    # MISMATCHED harness token still 401s. That's a config issue, not a
    # regression — skip with instructions, same philosophy as the 503 skip.
    probe = flow_ctx.get("/cms/legal", as_=admin)
    if probe.status_code == 401:
        pytest.skip(
            "harness ADMIN_TOKEN doesn't match the backend's — align "
            "tests/nl-harness/.env.local with the backend .env to run this flow"
        )
    assert probe.status_code == 200, probe.text

    # Parent starts clean on current versions.
    versions = {d["slug"]: d["required_version"] for d in _status(flow_ctx, parent)["documents"]}
    flow_ctx.post("/legal/accept", json={"versions": versions}, as_=parent)
    assert _status(flow_ctx, parent)["accepted_all"] is True

    # Capture the prior current so cleanup can restore its content.
    prior = flow_ctx.get("/content/legal/terms").json()
    run_tag = uuid4().hex[:8]

    def _restore() -> None:
        try:
            flow_ctx.put(
                "/cms/legal/terms/draft",
                json={"title": prior["title"], "body_md": prior["body_md"]},
                as_=admin,
            )
            flow_ctx.post(
                "/cms/legal/terms/publish",
                json={"version": f"restore-{run_tag}", "requires_reacceptance": False},
                as_=admin,
            )
        except Exception:
            pass  # best-effort; logged by FlowContext

    flow_ctx.register_cleanup(
        description="re-publish prior terms body (restore after harness publish)",
        fn=_restore,
    )

    # ── publish a re-acceptance version of terms ────────────────────
    draft = flow_ctx.put(
        "/cms/legal/terms/draft",
        json={"title": prior["title"], "body_md": f"{prior['body_md']}\n\n<!-- harness {run_tag} -->"},
        as_=admin,
    )
    assert draft.status_code == 200, draft.text
    publish = flow_ctx.post(
        "/cms/legal/terms/publish",
        json={"version": f"harness-{run_tag}", "requires_reacceptance": True},
        as_=admin,
    )
    assert publish.status_code == 200, publish.text
    assert publish.json()["is_current"] is True

    # ── exactly the changed slug re-prompts ─────────────────────────
    status = _status(flow_ctx, parent)
    assert status["needs"] == ["terms"], status
    # Prior version row is still in the history, unmodified.
    history = flow_ctx.get("/cms/legal/terms/versions", as_=admin).json()["versions"]
    prior_row = next(v for v in history if v["version"] == prior["version"])
    assert prior_row["body_md"] == prior["body_md"]
    assert prior_row["is_current"] is False

    # ── re-accept clears it ─────────────────────────────────────────
    reaccept = flow_ctx.post(
        "/legal/accept",
        json={"versions": {"terms": f"harness-{run_tag}"}},
        as_=parent,
    )
    assert reaccept.status_code == 200, reaccept.text
    assert _status(flow_ctx, parent)["accepted_all"] is True
