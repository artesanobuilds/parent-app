"""Circle conversations + invites (beta-v1 Phase 1).

The invariants this pins — all of them authorization, because this is the
surface that replaced an anonymous board with private group threads:

  • Participants see a conversation; NON-participants get 404 on every route
    (404, not 403 — a 403 confirms the thread exists).
  • A ONE-SIDED roster link grants nothing. Typing a stranger's user_id into
    your own household_members does not let you add them to a thread, and it
    does not let you read theirs.
  • Claiming an invite is what makes the link MUTUAL: it binds
    household_members.member_user_id on BOTH sides and fills in the pending
    circle_participants.user_id, at which point — and not before — the thread
    the inviter already created becomes visible to the invitee.
  • Owner-only actions (PATCH / DELETE / add participants) reject a mere
    participant.
  • delete_family removes the user's rows from all four Circle tables and
    leaves another household's conversation intact.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing
app.server; every TestClient block restores server.storage_backend in a
finally (a TestClient context exit closes the storage singleton).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "circle.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AUTH_RATE_PER_HOUR", "10000")
os.environ.setdefault("RATE_LIMIT_AUTH_PER_HOUR", "10000")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _parent(client, user_id, name):
    tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
    auth = {"Authorization": f"Bearer {tok}"}
    client.patch("/profile", json={"name": name}, headers=auth)
    return auth


def _add_member(client, auth, **body):
    r = client.post("/household/members", json=body, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()["member"]


def _link_mutually(server, a_auth, b_auth, client, *, a_id, b_id,
                   a_name="B Parent", b_name="A Parent"):
    """Both households hold a row pointing at the other — the mutual link
    circle_peer_ids requires."""
    mine = _add_member(client, a_auth, display_name=a_name, role="co_parent",
                       member_user_id=b_id)
    theirs = _add_member(client, b_auth, display_name=b_name, role="co_parent",
                         member_user_id=a_id)
    return mine, theirs


# --------------------------------------------------------------------------- #


def test_create_conversation_participants_see_it_strangers_get_404():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            owner = _parent(client, "cc-owner", "Ana Owner")
            peer = _parent(client, "cc-peer", "Ben Peer")
            stranger = _parent(client, "cc-stranger", "Eve Stranger")

            mine, _theirs = _link_mutually(
                client=client, server=server, a_auth=owner, b_auth=peer,
                a_id="cc-owner", b_id="cc-peer",
                a_name="Ben Peer", b_name="Ana Owner",
            )

            r = client.post("/circle/conversations", headers=owner, json={
                "title": "Saturday pickup", "body": "Who can cover 4pm?",
                "member_ids": [mine["id"]],
            })
            assert r.status_code == 200, r.text
            conv = r.json()
            conv_id = conv["id"]
            assert conv["title"] == "Saturday pickup"
            assert conv["owner_user_id"] == "cc-owner"
            assert conv["starter_is_me"] is True
            assert conv["starter_name"] == "Ana Owner"
            assert conv["reply_count"] == 0
            assert conv["last_reply_from"] is None
            assert conv["unread"] == 0
            # owner + the invited member
            assert len(conv["participants"]) == 2
            assert {p["user_id"] for p in conv["participants"]} == {"cc-owner", "cc-peer"}

            # the peer sees it in their list, and it is NOT theirs
            listed = client.get("/circle/conversations", headers=peer).json()
            assert [c["id"] for c in listed["conversations"]] == [conv_id]
            assert listed["conversations"][0]["starter_is_me"] is False
            assert listed["conversations"][0]["starter_name"] == "Ana Owner"

            # the peer replies; the owner sees the reply + an unread count
            r = client.post(f"/circle/conversations/{conv_id}/messages",
                            headers=peer, json={"body": "I can take it."})
            assert r.status_code == 200, r.text
            msg = r.json()
            assert msg["is_me"] is True and msg["author_name"] == "Ben Peer"
            assert msg["initials"] == "BP"

            detail = client.get(f"/circle/conversations/{conv_id}", headers=owner).json()
            assert detail["conversation"]["reply_count"] == 1
            assert detail["conversation"]["last_reply_from"] == "Ben Peer"
            assert detail["conversation"]["unread"] == 1
            assert [m["body"] for m in detail["messages"]] == ["I can take it."]
            assert detail["messages"][0]["is_me"] is False

            assert client.post(f"/circle/conversations/{conv_id}/read",
                               headers=owner).status_code == 200
            after = client.get(f"/circle/conversations/{conv_id}", headers=owner).json()
            assert after["conversation"]["unread"] == 0

            # THE STRANGER: 404 on every route, never 403 (which would confirm
            # the conversation exists).
            assert client.get("/circle/conversations",
                              headers=stranger).json()["conversations"] == []
            for method, path, body in [
                ("get", f"/circle/conversations/{conv_id}", None),
                ("patch", f"/circle/conversations/{conv_id}", {"title": "mine now"}),
                ("delete", f"/circle/conversations/{conv_id}", None),
                ("post", f"/circle/conversations/{conv_id}/messages", {"body": "hi"}),
                ("post", f"/circle/conversations/{conv_id}/participants",
                 {"member_ids": []}),
                ("post", f"/circle/conversations/{conv_id}/read", None),
            ]:
                kwargs = {"headers": stranger}
                if body is not None:
                    kwargs["json"] = body
                resp = getattr(client, method)(path, **kwargs)
                assert resp.status_code == 404, f"{method.upper()} {path} -> {resp.status_code}"

            # owner-only: a participant cannot edit or delete
            assert client.patch(f"/circle/conversations/{conv_id}", headers=peer,
                                json={"title": "hijacked"}).status_code == 403
            assert client.delete(f"/circle/conversations/{conv_id}",
                                 headers=peer).status_code == 403

            renamed = client.patch(f"/circle/conversations/{conv_id}", headers=owner,
                                   json={"title": "Sunday pickup"})
            assert renamed.status_code == 200
            assert renamed.json()["title"] == "Sunday pickup"

            assert client.delete(f"/circle/conversations/{conv_id}",
                                 headers=owner).json() == {"ok": True}
            assert client.get("/circle/conversations",
                              headers=peer).json()["conversations"] == []
    finally:
        _reconnect_shared_storage(server)


def test_one_sided_link_grants_nothing():
    """The hole this guard exists to close: adding a stranger's user_id to your
    OWN roster must not let you pull them into a thread and read their replies."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            grabber = _parent(client, "cc-grab", "Greta Grabber")
            victim = _parent(client, "cc-victim", "Vic Victim")

            # ONE-SIDED: only the grabber holds a row pointing at the victim.
            member = _add_member(client, grabber, display_name="Vic Victim",
                                 role="other", member_user_id="cc-victim")
            assert member["linked"] is True
            assert member["in_circle"] is False       # not mutual

            r = client.post("/circle/conversations", headers=grabber, json={
                "title": "Private", "body": "?", "member_ids": [member["id"]],
            })
            assert r.status_code == 403, r.text
            assert "mutual" in r.json()["detail"]

            # and the same rule on the add-participants route (a thread created
            # solo must not become a back door).
            solo = client.post("/circle/conversations", headers=grabber, json={
                "title": "Solo", "body": "", "member_ids": [],
            }).json()
            r = client.post(f"/circle/conversations/{solo['id']}/participants",
                            headers=grabber, json={"member_ids": [member["id"]]})
            assert r.status_code == 403, r.text
            assert client.get(f"/circle/conversations/{solo['id']}",
                              headers=victim).status_code == 404

            # a member id belonging to SOMEONE ELSE is a 404, not a 403
            r = client.post("/circle/conversations", headers=victim, json={
                "title": "x", "member_ids": [member["id"]],
            })
            assert r.status_code == 404
    finally:
        _reconnect_shared_storage(server)


def test_invite_claim_establishes_the_mutual_link_and_reveals_the_thread():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            inviter = _parent(client, "cc-inviter", "Ivy Inviter")
            assert client.patch("/profile/kids/Mateo", headers=inviter,
                                json={"age": 7}).status_code == 200
            invitee = _parent(client, "cc-invitee", "Nina Nanny")

            # An UNCLAIMED member: on the roster, no MVP account yet.
            nanny = _add_member(client, inviter, display_name="Nina Nanny",
                                role="nanny")
            assert nanny["member_user_id"] is None

            conv = client.post("/circle/conversations", headers=inviter, json={
                "title": "School run", "body": "Schedule below.",
                "member_ids": [nanny["id"]],
            }).json()
            conv_id = conv["id"]
            # She is listed, but her participant row has no account behind it —
            # so she cannot read a thing.
            assert any(p["member_id"] == nanny["id"] and p["user_id"] is None
                       for p in conv["participants"])
            assert client.get(f"/circle/conversations/{conv_id}",
                              headers=invitee).status_code == 404
            assert client.get("/circle/conversations",
                              headers=invitee).json()["conversations"] == []

            r = client.post("/circle/invites", headers=inviter,
                            json={"member_id": nanny["id"]})
            assert r.status_code == 200, r.text
            invite = r.json()
            token = invite["token"]
            assert invite["url"].endswith(f"/{token}")
            # Assert against the CONFIGURED base, not a literal domain. The
            # invite host is an unsettled product decision (it moved from the
            # mockup's unregistered share.mvparent.ai to the Railway host that
            # actually serves the claim page), and a hardcoded literal here turns
            # every future domain change into a spurious test failure. What
            # matters is that the URL comes from the one configured place.
            from app.circle import invite_base_url

            assert invite["url"] == f"{invite_base_url()}/{token}"
            assert invite["expires_at"]

            # Preview is UNAUTHENTICATED (the invitee may have no account yet)
            # and deliberately thin.
            preview = client.get(f"/circle/invites/{token}")
            assert preview.status_code == 200, preview.text
            preview = preview.json()
            assert preview["inviter_name"] == "Ivy Inviter"
            assert preview["household_label"] == "Ivy's household"
            assert preview["kids_label"] == "Mateo"
            assert preview["expired"] is False and preview["claimed"] is False

            claimed = client.post(f"/circle/invites/{token}/claim", headers=invitee)
            assert claimed.status_code == 200, claimed.text
            claimed = claimed.json()
            assert claimed["ok"] is True
            assert claimed["member_id"] == nanny["id"]
            assert claimed["inviter_user_id"] == "cc-inviter"

            # BOTH sides bound -> mutual link -> the thread is now visible.
            storage = server.storage_backend
            assert "cc-invitee" in storage.circle_peer_ids("cc-inviter")
            assert "cc-inviter" in storage.circle_peer_ids("cc-invitee")

            listed = client.get("/circle/conversations", headers=invitee).json()
            assert [c["id"] for c in listed["conversations"]] == [conv_id]
            assert client.post(f"/circle/conversations/{conv_id}/messages",
                               headers=invitee,
                               json={"body": "On it."}).status_code == 200

            assert client.get(f"/circle/invites/{token}").json()["claimed"] is True
            # Re-claiming by a DIFFERENT account is refused.
            other = _parent(client, "cc-other", "Otto Other")
            assert client.post(f"/circle/invites/{token}/claim",
                               headers=other).status_code == 409
            assert client.get("/circle/invites/nope-not-a-token").status_code == 404
    finally:
        _reconnect_shared_storage(server)


def test_invite_base_url_is_configurable(monkeypatch):
    from app import circle

    monkeypatch.setenv(circle.INVITE_BASE_URL_ENV, "https://example.test/join/")
    assert circle.invite_base_url() == "https://example.test/join"
    monkeypatch.delenv(circle.INVITE_BASE_URL_ENV)
    assert circle.invite_base_url() == circle.DEFAULT_INVITE_BASE_URL


def test_delete_family_clears_all_four_circle_tables_and_spares_others():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            doomed = _parent(client, "cc-del-a", "Dana Doomed")
            peer = _parent(client, "cc-del-b", "Pat Peer")
            other = _parent(client, "cc-del-c", "Ora Other")
            other2 = _parent(client, "cc-del-d", "Ola Other")

            mine, _ = _link_mutually(
                client=client, server=server, a_auth=doomed, b_auth=peer,
                a_id="cc-del-a", b_id="cc-del-b",
                a_name="Pat Peer", b_name="Dana Doomed",
            )
            other_mine, _ = _link_mutually(
                client=client, server=server, a_auth=other, b_auth=other2,
                a_id="cc-del-c", b_id="cc-del-d",
                a_name="Ola Other", b_name="Ora Other",
            )

            doomed_conv = client.post("/circle/conversations", headers=doomed, json={
                "title": "Mine", "body": "b", "member_ids": [mine["id"]],
            }).json()
            client.post(f"/circle/conversations/{doomed_conv['id']}/messages",
                        headers=peer, json={"body": "reply"})
            client.post("/circle/invites", headers=doomed,
                        json={"member_id": mine["id"]})

            # An untouched household, plus a thread the doomed user merely
            # JOINED (it must survive, minus their participation).
            untouched = client.post("/circle/conversations", headers=other, json={
                "title": "Theirs", "body": "b", "member_ids": [other_mine["id"]],
            }).json()
            client.post(f"/circle/invites", headers=other,
                        json={"member_id": other_mine["id"]})

            storage = server.storage_backend
            counts = storage.delete_family(user_id="cc-del-a", actor="test")["counts"]
            assert counts["circle_conversations"] == 1
            assert counts["circle_messages"] >= 1
            assert counts["circle_participants"] >= 2
            assert counts["invite_tokens"] == 1

            def rows(table, where, params):
                return storage._con.execute(
                    f"SELECT count(*) FROM {table} WHERE {where}", params
                ).fetchone()[0]

            assert rows("circle_conversations", "owner_user_id = ?", ["cc-del-a"]) == 0
            assert rows("circle_participants", "user_id = ?", ["cc-del-a"]) == 0
            assert rows("circle_messages", "user_id = ?", ["cc-del-a"]) == 0
            assert rows("invite_tokens", "user_id = ?", ["cc-del-a"]) == 0
            assert rows("circle_participants", "conversation_id = ?",
                        [doomed_conv["id"]]) == 0
            assert rows("circle_messages", "conversation_id = ?",
                        [doomed_conv["id"]]) == 0

            # the other household is untouched
            assert rows("circle_conversations", "id = ?", [untouched["id"]]) == 1
            assert rows("circle_participants", "conversation_id = ?",
                        [untouched["id"]]) == 2
            assert rows("invite_tokens", "user_id = ?", ["cc-del-c"]) == 1
            still = client.get("/circle/conversations", headers=other).json()
            assert [c["id"] for c in still["conversations"]] == [untouched["id"]]
    finally:
        _reconnect_shared_storage(server)


def test_retired_surfaces_leave_no_routes_and_no_tables():
    """The community board and 1:1 DMs are fully retired: routes withdrawn
    first, then the five tables dropped in migration v21.

    The DDL was deleted alongside the migration — this is what catches a
    re-added `CREATE TABLE IF NOT EXISTS`, which would run BEFORE migrations on
    every boot and silently resurrect an empty table that v21 (already stamped)
    never drops again."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            for method, path in [
                ("get", "/content/community"),
                ("get", "/content/community/cp-retired-1"),
                ("get", "/content/community/cp-retired-1/replies"),
                ("get", "/dm/members"),
                ("get", "/dm/conversations"),
                ("post", "/dm/conversations"),
            ]:
                resp = getattr(client, method)(
                    path, **({"json": {}} if method == "post" else {})
                )
                assert resp.status_code == 404, f"{path}: {resp.status_code}"
            assert client.post("/content/community/new", json={}).status_code == 404

            live = {
                r[0] for r in server.storage_backend._con.execute(
                    "SELECT table_name FROM information_schema.tables"
                ).fetchall()
            }
            for table in ("community_posts", "post_replies", "dm_conversations",
                          "dm_messages", "dm_reactions"):
                assert table not in live, f"{table} was dropped in v21 but is back"
    finally:
        _reconnect_shared_storage(server)


def test_every_circle_route_goes_through_the_one_guard():
    """Structural: any /circle/conversations route that forgets
    `_conversation_or_404` (or its owner-only wrapper) is a scoping hole the
    unit tests above would not necessarily catch — a new route added later
    would simply be untested. Grep the source instead."""
    src = (BACKEND_ROOT / "app" / "circle.py").read_text()
    bodies = src.split("@router.")
    missing = []
    for chunk in bodies[1:]:
        header = chunk.split("\n", 1)[0]
        if "/conversations/{conversation_id}" not in header:
            continue
        if "_conversation_or_404" not in chunk.split("@router.")[0]:
            missing.append(header)
    assert not missing, f"routes bypassing the Circle guard: {missing}"


def test_circle_payload_matches_the_ios_contract():
    """Cross-surface lock, mirroring test_planner_sprint2's board-payload test.

    The planner payload silently drifted when the backend and iOS were built in
    parallel: strict Codable yields nil on a missing key, so a renamed field
    renders as an EMPTY section rather than an error, and looks like a design
    choice. Circle was built the same way, in the same session, and had no such
    guard — this adds it.

    The expected keys are READ OUT OF `CircleModels.swift` rather than duplicated
    here, in the same grep-the-iOS-source style as test_ios_baseurl_guard, so
    renaming a field on either side fails this test instead of quietly emptying a
    screen.
    """
    import re

    from fastapi.testclient import TestClient

    import app.server as server

    ios_models = BACKEND_ROOT.parent / "mvp" / "MVP" / "CircleModels.swift"
    assert ios_models.exists(), f"missing {ios_models}"
    swift = ios_models.read_text()
    mapped = set(re.findall(r'case\s+\w+\s*=\s*"([^"]+)"', swift))
    assert "reply_count" in mapped and "starter_is_me" in mapped, (
        "CircleModels.swift no longer declares the keys this test was written "
        "against — re-read it before trusting this assertion"
    )

    _reconnect_shared_storage(server)

    with TestClient(server.app) as client:
        alice = _parent(client, "ios-contract-alice", "Alice Contract")
        rosa = _parent(client, "ios-contract-rosa", "Rosa Contract")
        mine, _theirs = _link_mutually(
            server, alice, rosa, client,
            a_id="ios-contract-alice", b_id="ios-contract-rosa",
            a_name="Rosa Contract", b_name="Alice Contract",
        )

        created = client.post("/circle/conversations", headers=alice, json={
            "title": "Dinner with Ben & Lily",
            "body": "I need dinner ideas for the kids tonight.",
            "member_ids": [mine["id"]],
        })
        assert created.status_code == 200, created.text
        conv = created.json()
        conv_id = conv["id"]

        # Conversation: every key iOS decodes must be present on the wire.
        for key in ("id", "title", "body", "owner_user_id", "created_at",
                    "last_reply_at", "reply_count", "last_reply_from",
                    "starter_name", "starter_is_me", "unread", "participants"):
            assert key in conv, f"conversation payload is missing `{key}` (iOS decodes it)"

        assert conv["participants"], "a new conversation has no participants"
        for p in conv["participants"]:
            for key in ("user_id", "member_id", "display_name", "initials"):
                assert key in p, f"participant is missing `{key}`"

        posted = client.post(f"/circle/conversations/{conv_id}/messages",
                             headers=rosa, json={"body": "Waffles."})
        assert posted.status_code == 200, posted.text
        for key in ("id", "user_id", "author_name", "initials", "body",
                    "created_at", "is_me"):
            assert key in posted.json(), f"message payload is missing `{key}`"

        thread = client.get(f"/circle/conversations/{conv_id}", headers=alice)
        assert thread.status_code == 200, thread.text
        assert "conversation" in thread.json() and "messages" in thread.json(), (
            "the thread route must return {conversation, messages} — iOS decodes "
            "CircleThreadResponse with exactly those two keys"
        )

        inv = client.post("/circle/invites", headers=alice, json={"member_id": mine["id"]})
        assert inv.status_code == 200, inv.text
        for key in ("token", "url", "expires_at"):
            assert key in inv.json(), f"invite payload is missing `{key}`"

        prev = client.get(f"/circle/invites/{inv.json()['token']}")
        assert prev.status_code == 200, prev.text
        for key in ("inviter_name", "household_label", "kids_label",
                    "expired", "claimed"):
            assert key in prev.json(), f"invite preview is missing `{key}`"
