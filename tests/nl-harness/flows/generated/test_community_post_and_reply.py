# flows/generated/test_community_post_and_reply.py
#
# @generated_from: specs/tier-1/community-post-and-reply.flow.yml
# @generated_at: 2026-05-31T15:00:00Z
# @modules: auth, community
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_post_and_reply_roundtrip(flow_ctx, existing_parent):
    parent = existing_parent

    # ── Step 1: create a community post as the author ───────────────
    create_resp = flow_ctx.post(
        "/content/community/new",
        json={
            "category": "parenting-stress",
            "title": "nl-harness: test post",
            "preview": "This is an automated harness post; safe to ignore.",
            "user_id": parent.user_id,
            "author_name": parent.display_name,
        },
        as_=parent,
    )
    assert create_resp.status_code == 200, create_resp.text
    post = create_resp.json()
    for key in ("id", "category", "title", "preview"):
        assert key in post, f"post response missing {key!r}: {post}"
    post_id = post["id"]
    assert post_id.startswith("cp-"), f"expected id prefix `cp-`, got {post_id!r}"

    # ── Step 2: created post appears in the community list ──────────
    list_resp = flow_ctx.get("/content/community")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert isinstance(listed, list)
    assert any(p.get("id") == post_id for p in listed), \
        f"created post {post_id!r} not found in /content/community list"

    # ── Step 3: category filter returns the post ────────────────────
    cat_list_resp = flow_ctx.get(
        "/content/community", params={"category": "parenting-stress"},
    )
    assert cat_list_resp.status_code == 200
    cat_listed = cat_list_resp.json()
    assert any(p.get("id") == post_id for p in cat_listed), \
        "post not found when filtering by its own category"
    for p in cat_listed:
        assert p["category"] == "parenting-stress", \
            f"category filter leaked post in category {p['category']!r}"

    # ── Step 4: reply round-trip ────────────────────────────────────
    reply_body = "nl-harness: automated reply"
    reply_resp = flow_ctx.post(
        f"/content/community/{post_id}/replies",
        json={
            "user_id": parent.user_id,
            "author_name": parent.display_name,
            "body": reply_body,
        },
        as_=parent,
    )
    assert reply_resp.status_code == 200, reply_resp.text
    reply = reply_resp.json()
    for key in ("id", "post_id", "body"):
        assert key in reply, f"reply response missing {key!r}: {reply}"
    assert reply["post_id"] == post_id
    assert reply["body"] == reply_body

    replies_resp = flow_ctx.get(f"/content/community/{post_id}/replies")
    assert replies_resp.status_code == 200
    replies = replies_resp.json()
    assert any(r.get("id") == reply["id"] for r in replies), \
        "newly-created reply not in /replies list"


def test_anonymous_community_writes_are_rejected(flow_ctx):
    """The auth gate landed 2026-07: unauthenticated community writes 401
    (previously an impersonation + spam vector — caller chose user_id/author)."""
    post_resp = flow_ctx.post(
        "/content/community/new",
        json={
            "category": "parenting-stress",
            "title": "anon-attempted",
            "preview": "should not be allowed",
            "user_id": "anon-no-token",
            "author_name": "Anon",
        },
    )
    assert post_resp.status_code == 401, \
        f"expected 401 for unauthenticated community post; got {post_resp.status_code}"

    reply_resp = flow_ctx.post(
        "/content/community/cp-does-not-matter/replies",
        json={"user_id": "anon-no-token", "author_name": "Anon", "body": "nope"},
    )
    assert reply_resp.status_code == 401, \
        f"expected 401 for unauthenticated reply; got {reply_resp.status_code}"
