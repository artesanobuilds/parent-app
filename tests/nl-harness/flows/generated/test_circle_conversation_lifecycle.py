# flows/generated/test_circle_conversation_lifecycle.py
#
# @generated_from: specs/tier-1/circle-conversation-lifecycle.flow.yml
# @generated_at: 2026-08-07T19:00:00Z
# @modules: circle, household, auth, profile
# @promoted_by: (none -- awaiting review)
#
# Replaces test_dm_conversation_lifecycle.py. The public board and 1:1 DMs were
# retired in the beta-v1 sprint-2 redesign (migration v21 dropped
# community_posts, post_replies and all three dm_* tables), so the old flow
# tested endpoints that now 404.
#
import pytest

from lib.personas.new_parent import new_parent as make_parent

pytestmark = pytest.mark.tier1


def _name(flow_ctx, parent, name):
    resp = flow_ctx.patch("/profile", json={"name": name}, as_=parent)
    assert resp.status_code == 200, resp.text


def _add_member(flow_ctx, owner, *, display_name, role, member_user_id=None):
    """Put someone on the owner's roster. Without `member_user_id` this is a
    pure address-book entry — no account, no access."""
    payload = {"display_name": display_name, "role": role}
    if member_user_id:
        payload["member_user_id"] = member_user_id
    resp = flow_ctx.post("/household/members", json=payload, as_=owner)
    assert resp.status_code == 200, resp.text
    # The route wraps the row: {"member": {...}} — not a bare object.
    return resp.json()["member"]


def test_retired_surfaces_are_gone(flow_ctx, new_parent):
    """The board and DM routes must be ABSENT, not merely unused.

    Asserted here rather than assumed: a re-added route would silently restore a
    surface whose backing tables were dropped, and the failure would show up as
    a 500 in front of a parent.
    """
    assert flow_ctx.get("/dm/conversations", as_=new_parent).status_code == 404
    assert flow_ctx.get("/dm/members", as_=new_parent).status_code == 404
    assert flow_ctx.get("/content/community").status_code == 404


def test_circle_starts_empty_and_requires_auth(flow_ctx, new_parent):
    assert flow_ctx.get("/circle/conversations").status_code == 401

    convs = flow_ctx.get("/circle/conversations", as_=new_parent)
    assert convs.status_code == 200, convs.text
    assert convs.json()["conversations"] == []

    roles = flow_ctx.get("/household/roles", as_=new_parent)
    assert roles.status_code == 200, roles.text
    assert "nanny" in str(roles.json()), "the roster must offer a nanny role"

    # No title → refused, not silently created.
    bad = flow_ctx.post("/circle/conversations",
                        json={"title": "", "body": "", "member_ids": []}, as_=new_parent)
    assert bad.status_code == 400, bad.text
    assert flow_ctx.get("/circle/conversations/does-not-exist",
                        as_=new_parent).status_code == 404


def test_a_one_sided_link_grants_nothing(flow_ctx, new_parent):
    """The load-bearing privacy property.

    Mallory types Alice's user_id into her OWN roster. That must buy her
    nothing: if a one-sided row were enough, anyone could add an id they
    obtained and pull that family into a conversation they control.
    """
    alice = new_parent
    mallory = make_parent(flow_ctx)
    _name(flow_ctx, alice, "Alice Harness")
    _name(flow_ctx, mallory, "Mallory Harness")

    stolen = _add_member(flow_ctx, mallory, display_name="Alice Harness",
                         role="neighbour", member_user_id=alice.user_id)

    refused = flow_ctx.post("/circle/conversations",
                            json={"title": "Let me in", "body": "hi",
                                  "member_ids": [stolen["id"]]}, as_=mallory)
    assert refused.status_code == 403, (
        "a NON-mutual link let a stranger open a conversation with Alice "
        f"(got {refused.status_code}): {refused.text}"
    )

    # And Alice's own view is untouched by Mallory's roster.
    assert flow_ctx.get("/circle/conversations", as_=alice).json()["conversations"] == []


def test_invite_claim_then_conversation(flow_ctx, new_parent):
    alice = new_parent
    rosa = make_parent(flow_ctx)
    mallory = make_parent(flow_ctx)
    _name(flow_ctx, alice, "Alice Harness")
    _name(flow_ctx, rosa, "Rosa Harness")
    _name(flow_ctx, mallory, "Mallory Harness")

    # ── an unclaimed roster entry is an address-book row only ────────
    member = _add_member(flow_ctx, alice, display_name="Rosa", role="nanny")
    roster = flow_ctx.get("/household/members", as_=alice)
    assert roster.status_code == 200, roster.text
    assert any(m["id"] == member["id"] for m in roster.json()["members"])

    # ── invite: URL comes from config, never a hardcoded domain ──────
    inv = flow_ctx.post("/circle/invites", json={"member_id": member["id"]}, as_=alice)
    assert inv.status_code == 200, inv.text
    token = inv.json()["token"]
    assert token and inv.json()["url"].endswith(token)

    # Preview is PUBLIC (the invitee has no account yet) and must not leak ids.
    prev = flow_ctx.get(f"/circle/invites/{token}")
    assert prev.status_code == 200, prev.text
    body = prev.json()
    assert body["inviter_name"] == "Alice Harness"
    assert body["claimed"] is False and body["expired"] is False
    assert alice.user_id not in prev.text, "the invite preview leaks the inviter's user_id"
    assert flow_ctx.get("/circle/invites/not-a-real-token").status_code == 404

    # ── claim binds BOTH sides from one call ─────────────────────────
    claimed = flow_ctx.post(f"/circle/invites/{token}/claim", as_=rosa)
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["inviter_user_id"] == alice.user_id
    assert flow_ctx.get(f"/circle/invites/{token}").json()["claimed"] is True

    # A second account cannot take a used seat.
    assert flow_ctx.post(f"/circle/invites/{token}/claim",
                         as_=mallory).status_code == 409

    # ── the conversation ────────────────────────────────────────────
    conv = flow_ctx.post("/circle/conversations",
                         json={"title": "Dinner with Ben & Lily",
                               "body": "I need dinner ideas for the kids tonight.",
                               "member_ids": [member["id"]]}, as_=alice)
    assert conv.status_code == 200, conv.text
    conv_id = conv.json()["id"]
    assert conv.json()["starter_is_me"] is True
    assert conv.json()["reply_count"] == 0

    # Rosa sees it because the link is now mutual.
    rosa_list = flow_ctx.get("/circle/conversations", as_=rosa).json()["conversations"]
    assert [c["id"] for c in rosa_list] == [conv_id], (
        "a claimed member cannot see the conversation they were added to"
    )
    assert rosa_list[0]["starter_is_me"] is False
    assert rosa_list[0]["starter_name"] == "Alice Harness"

    # ── replies move reply_count / unread; own post is never unread ──
    reply = flow_ctx.post(f"/circle/conversations/{conv_id}/messages",
                          json={"body": "Waffles. Always waffles."}, as_=rosa)
    assert reply.status_code == 200, reply.text
    assert reply.json()["is_me"] is True

    alice_view = flow_ctx.get("/circle/conversations", as_=alice).json()["conversations"][0]
    assert alice_view["reply_count"] == 1
    assert alice_view["unread"] >= 1
    assert alice_view["last_reply_from"] == "Rosa Harness"

    rosa_view = flow_ctx.get("/circle/conversations", as_=rosa).json()["conversations"][0]
    assert rosa_view["unread"] == 0, "the poster's own message is unread to them"

    flow_ctx.post(f"/circle/conversations/{conv_id}/read", as_=alice)
    assert flow_ctx.get("/circle/conversations",
                        as_=alice).json()["conversations"][0]["unread"] == 0

    # ── outsider isolation: 404 on EVERY path, never 403 ────────────
    for method, path, payload in (
        ("get", f"/circle/conversations/{conv_id}", None),
        ("post", f"/circle/conversations/{conv_id}/messages", {"body": "let me in"}),
        ("post", f"/circle/conversations/{conv_id}/read", {}),
        ("patch", f"/circle/conversations/{conv_id}", {"title": "mine now"}),
        ("delete", f"/circle/conversations/{conv_id}", None),
    ):
        fn = getattr(flow_ctx, method)
        resp = fn(path, as_=mallory) if payload is None else fn(path, json=payload, as_=mallory)
        assert resp.status_code == 404, (
            f"{method.upper()} {path} returned {resp.status_code} to a "
            "non-participant — 404 only, or existence is confirmed"
        )

    # ── owner-only mutations ────────────────────────────────────────
    # Note the deliberate split in status codes, verified above and here:
    #   • an OUTSIDER gets 404 — existence must not be confirmed
    #   • a PARTICIPANT who isn't the owner gets 403 — they can already see the
    #     thread, so hiding it buys nothing and 404 would just be confusing
    assert flow_ctx.patch(f"/circle/conversations/{conv_id}",
                          json={"title": "Renamed by a guest"},
                          as_=rosa).status_code == 403
    assert flow_ctx.delete(f"/circle/conversations/{conv_id}", as_=rosa).status_code == 403
    renamed = flow_ctx.patch(f"/circle/conversations/{conv_id}",
                             json={"title": "Dinner plans for the kids"}, as_=alice)
    assert renamed.status_code == 200 and renamed.json()["title"] == "Dinner plans for the kids"

    # ── history is not truncated at join time ───────────────────────
    thread = flow_ctx.get(f"/circle/conversations/{conv_id}", as_=rosa)
    assert thread.status_code == 200, thread.text
    assert len(thread.json()["messages"]) >= 1, (
        "a member added after the first post cannot see the history"
    )

    # ── deleting the owner's family removes it for everyone ─────────
    assert flow_ctx.delete(f"/family/{alice.user_id}", as_=alice).status_code == 200
    after = flow_ctx.get("/circle/conversations", as_=rosa)
    assert after.status_code == 200, after.text
    assert after.json()["conversations"] == [], (
        "a participant still sees a conversation whose owner deleted their family"
    )
