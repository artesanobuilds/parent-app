# flows/generated/test_saved_items_lifecycle.py
#
# @generated_from: specs/tier-1/saved-items-lifecycle.flow.yml
# @generated_at: 2026-07-19T02:00:00Z
# @modules: saved, content, auth
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_saved_items_lifecycle(flow_ctx, new_parent):
    parent = new_parent

    articles = flow_ctx.get("/content/articles").json()
    if not articles:
        pytest.skip("no articles seeded on this backend")
    article_id = articles[0]["id"]

    # ── anonymous gate ──────────────────────────────────────────────
    assert flow_ctx.get("/saved").status_code == 401

    # ── article save: server-side snapshot ──────────────────────────
    r = flow_ctx.post("/saved", json={
        "item_type": "article", "item_ref": article_id,
        "context": {"surface": "harness"},
    }, as_=parent)
    assert r.status_code == 200, r.text
    assert r.json()["title"] == articles[0]["title"]
    assert r.json()["save_count"] == 1

    # bad inputs
    assert flow_ctx.post("/saved", json={"item_type": "article", "item_ref": "no-such"},
                         as_=parent).status_code == 404
    assert flow_ctx.post("/saved", json={"item_type": "bogus", "item_ref": "x"},
                         as_=parent).status_code == 400
    assert flow_ctx.post("/saved", json={"item_type": "coach_reply", "item_ref": "m1"},
                         as_=parent).status_code == 400  # body required

    # ── coach reply carries its snapshot ────────────────────────────
    r = flow_ctx.post("/saved", json={
        "item_type": "coach_reply", "item_ref": "harness-msg-1",
        "body": "One thing to try tonight: name the feeling before the fix.",
    }, as_=parent)
    assert r.status_code == 200 and r.json()["body"].startswith("One thing")

    # ── refs drive bookmark state ───────────────────────────────────
    refs = flow_ctx.get("/saved/refs", params={"item_type": "article"}, as_=parent).json()["refs"]
    assert refs == [article_id]

    # ── soft unsave → gone from refs → re-save revives with count 2 ─
    r = flow_ctx.delete(f"/saved?item_type=article&item_ref={article_id}", as_=parent)
    assert r.status_code == 200 and r.json()["unsaved"] is True
    assert flow_ctx.get("/saved/refs", params={"item_type": "article"},
                        as_=parent).json()["refs"] == []
    r = flow_ctx.post("/saved", json={"item_type": "article", "item_ref": article_id},
                      as_=parent)
    assert r.json()["save_count"] == 2

    # ── merged list, newest first ───────────────────────────────────
    items = flow_ctx.get("/saved", as_=parent).json()["items"]
    kinds = {i["item_type"] for i in items}
    assert {"article", "coach_reply"} <= kinds
    assert all(i.get("origin") in ("saved", "plan") for i in items)

    # ── deletion takes the saves ────────────────────────────────────
    r = flow_ctx.delete(f"/family/{parent.user_id}", as_=parent)
    assert r.status_code == 200
    assert r.json()["deleted"].get("saved_items", 0) >= 2
