# flows/generated/test_dm_conversation_lifecycle.py
#
# @generated_from: specs/tier-1/dm-conversation-lifecycle.flow.yml
# @generated_at: 2026-07-19T00:00:00Z
# @modules: dm, auth, profile
# @promoted_by: (none -- awaiting review)
#
import pytest

from lib.personas.new_parent import new_parent as make_parent

pytestmark = pytest.mark.tier1


def _name(flow_ctx, parent, name):
    resp = flow_ctx.patch("/profile", json={"name": name}, as_=parent)
    assert resp.status_code == 200, resp.text


def test_dm_conversation_lifecycle(flow_ctx, new_parent):
    alice = new_parent
    bob = make_parent(flow_ctx)
    mallory = make_parent(flow_ctx)
    _name(flow_ctx, alice, "Alice Harness")
    _name(flow_ctx, bob, "Bob Harness")
    _name(flow_ctx, mallory, "Mallory Harness")

    # ── directory: they can find each other, never themselves ───────
    members = flow_ctx.get("/dm/members", as_=alice).json()["members"]
    ids = {m["user_id"] for m in members}
    assert bob.user_id in ids and alice.user_id not in ids

    # ── canonical pair ──────────────────────────────────────────────
    c1 = flow_ctx.post("/dm/conversations", json={"peer_user_id": bob.user_id}, as_=alice)
    assert c1.status_code == 200, c1.text
    c2 = flow_ctx.post("/dm/conversations", json={"peer_user_id": alice.user_id}, as_=bob)
    conv_id = c1.json()["id"]
    assert conv_id == c2.json()["id"], "A->B and B->A must be ONE conversation"
    assert c1.json()["peer_name"] == "Bob Harness"

    # ── message → unread → read ─────────────────────────────────────
    sent = flow_ctx.post(f"/dm/conversations/{conv_id}/messages",
                         json={"body": "Hi from the harness"}, as_=alice)
    assert sent.status_code == 200, sent.text
    inbox_bob = flow_ctx.get("/dm/conversations", as_=bob).json()
    assert inbox_bob["total_unread"] == 1
    assert inbox_bob["conversations"][0]["last_message_preview"] == "Hi from the harness"
    assert flow_ctx.get("/dm/conversations", as_=alice).json()["total_unread"] == 0
    flow_ctx.post(f"/dm/conversations/{conv_id}/read", as_=bob)
    assert flow_ctx.get("/dm/conversations", as_=bob).json()["total_unread"] == 0

    # ── outsider isolation: 404 everywhere, never 403 ───────────────
    assert flow_ctx.get(f"/dm/conversations/{conv_id}/messages", as_=mallory).status_code == 404
    assert flow_ctx.post(f"/dm/conversations/{conv_id}/messages",
                         json={"body": "let me in"}, as_=mallory).status_code == 404
    assert flow_ctx.post(f"/dm/conversations/{conv_id}/block", as_=mallory, json={}).status_code == 404

    # ── block / unblock ─────────────────────────────────────────────
    flow_ctx.post(f"/dm/conversations/{conv_id}/block", json={}, as_=bob)
    assert flow_ctx.post(f"/dm/conversations/{conv_id}/messages",
                         json={"body": "hello?"}, as_=alice).status_code == 403
    flow_ctx.post(f"/dm/conversations/{conv_id}/unblock", json={}, as_=bob)
    assert flow_ctx.post(f"/dm/conversations/{conv_id}/messages",
                         json={"body": "back on"}, as_=bob).status_code == 200

    # ── report ──────────────────────────────────────────────────────
    assert flow_ctx.post(f"/dm/conversations/{conv_id}/report",
                         json={"note": "harness report"}, as_=alice).status_code == 200

    # ── deletion removes the thread from BOTH inboxes ───────────────
    assert flow_ctx.delete(f"/family/{alice.user_id}", as_=alice).status_code == 200
    inbox_bob_after = flow_ctx.get("/dm/conversations", as_=bob).json()
    assert inbox_bob_after["conversations"] == [], (
        "peer inbox still lists a thread with a deleted family"
    )
