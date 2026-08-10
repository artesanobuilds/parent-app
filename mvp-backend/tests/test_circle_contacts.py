"""Circle contacts by email + the request/accept consent step (sprint 2 Phase B).

"If you type in an email address and that person already exists in the system,
no need to invite them — just pull them from the system."

Pulling them in is an AUTHORIZATION change, so this file pins the two properties
that make it safe:

  • **No enumeration oracle.** `POST /circle/contacts` returns the IDENTICAL
    status and body for an email that belongs to an MVP user and one that
    belongs to nobody. That single assertion is the whole security property —
    the response must not become a "does this person use MVP?" lookup.
  • **No link without consent.** A match creates a PENDING request and nothing
    else. Until the recipient accepts, the requester cannot list, read, or post
    to any of their conversations, and `circle_peer_ids` does not include them.
    Accept binds BOTH directions (through the same helper `claim_invite` uses);
    decline binds nothing.

Plus the ownership boundary — only the `to_user_id` may accept or decline, and
anyone else gets 404 (not 403: a 403 confirms the request exists) — and the
duplicate-pending guard, which is enforced in code because DuckDB has no
partial unique index.

A throwaway DuckDB file is selected via MVP_DUCKDB_PATH before importing
app.server; NEVER ":memory:" (that's a process-wide shared connection here and
rows leak between tests). Every TestClient block restores
server.storage_backend in a finally (a TestClient context exit closes the
storage singleton).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH",
                      str(Path(tempfile.mkdtemp()) / "circle_contacts.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("RATE_LIMIT_AUTH_PER_HOUR", "100000")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _parent(client, user_id, name):
    tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
    auth = {"Authorization": f"Bearer {tok}"}
    client.patch("/profile", json={"name": name}, headers=auth)
    return auth


def _give_identity(server, user_id: str, email: str, *, provider: str = "apple") -> None:
    """Attach an auth identity so the email lookup can find this account.

    Written directly because the real path is an OAuth round-trip. Mixed case on
    purpose in some callers: `auth_identities.email` is NOT lowercased on write
    (app/migrations.py:183), which is exactly why the lookup normalizes."""
    import uuid

    server.storage_backend._con.execute(
        "INSERT INTO auth_identities (id, user_id, provider, provider_sub, email, "
        "email_verified, created_at) VALUES (?, ?, ?, ?, ?, true, now())",
        [uuid.uuid4().hex, user_id, provider, uuid.uuid4().hex, email],
    )


# --------------------------------------------------------------------------- #
# The security property: one response shape, whatever the answer
# --------------------------------------------------------------------------- #


def test_known_and_unknown_emails_get_byte_identical_responses():
    """THE test. If these two ever diverge — status, keys, or values — the
    endpoint has become an oracle for "is this email an MVP user?", and anyone
    with a token can enumerate the user base one address at a time."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-asker", "Ana Asker")
            _parent(client, "ct-known", "Ben Known")
            _give_identity(server, "ct-known", "ben.known@example.com")

            hit = client.post("/circle/contacts",
                              json={"email": "ben.known@example.com"}, headers=asker)
            miss = client.post("/circle/contacts",
                               json={"email": "nobody-at-all@example.com"}, headers=asker)

            assert hit.status_code == miss.status_code == 200, (hit.text, miss.text)
            assert hit.json() == miss.json() == {"status": "sent"}, (
                "the matched and unmatched paths returned different bodies — "
                "POST /circle/contacts is now an email-enumeration oracle"
            )

            # And the two paths really did do different things underneath, so
            # the assertion above is meaningful rather than vacuous.
            requests = server.storage_backend._con.execute(
                "SELECT to_user_id FROM circle_requests WHERE from_user_id = ?",
                ["ct-asker"],
            ).fetchall()
            assert requests == [("ct-known",)], (
                "the matched email should have created exactly one pending request"
            )
            invites = server.storage_backend._con.execute(
                "SELECT count(*) FROM invite_tokens WHERE user_id = ?", ["ct-asker"],
            ).fetchone()[0]
            assert invites == 1, "the unmatched email should have minted an invite token"
    finally:
        _reconnect_shared_storage(server)


def test_the_lookup_normalizes_case_and_whitespace():
    """`auth_identities.email` is stored as the provider sent it — mixed case,
    sometimes padded. A parent typing the same address differently must still
    reach the same account (and still learn nothing about it)."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-norm-asker", "Ana Asker")
            _parent(client, "ct-norm-target", "Cara Target")
            _give_identity(server, "ct-norm-target", "Cara.Target@Example.COM")

            r = client.post("/circle/contacts",
                            json={"email": "  cara.target@example.com "}, headers=asker)
            assert r.status_code == 200 and r.json() == {"status": "sent"}

            rows = server.storage_backend._con.execute(
                "SELECT to_user_id FROM circle_requests WHERE from_user_id = ?",
                ["ct-norm-asker"],
            ).fetchall()
            assert rows == [("ct-norm-target",)], (
                "case/whitespace differences broke the match — the lookup must "
                "normalize lower(trim(email)) on both sides"
            )
    finally:
        _reconnect_shared_storage(server)


def test_an_ambiguous_email_is_treated_as_no_match():
    """Two accounts sharing an address is a real state (nothing makes
    `auth_identities.email` unique). Auto-linking on a fuzzy hit would put a
    parent next to the WRONG family, so zero and many are one outcome."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-amb-asker", "Ana Asker")
            _parent(client, "ct-amb-one", "One Parent")
            _parent(client, "ct-amb-two", "Two Parent")
            _give_identity(server, "ct-amb-one", "shared@example.com", provider="apple")
            _give_identity(server, "ct-amb-two", "shared@example.com", provider="google")

            r = client.post("/circle/contacts",
                            json={"email": "shared@example.com"}, headers=asker)
            assert r.status_code == 200 and r.json() == {"status": "sent"}

            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests WHERE from_user_id = ?",
                ["ct-amb-asker"],
            ).fetchone()[0] == 0, "an ambiguous email auto-linked a family"
            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM invite_tokens WHERE user_id = ?",
                ["ct-amb-asker"],
            ).fetchone()[0] == 1, "the ambiguous case should fall back to an invite"
    finally:
        _reconnect_shared_storage(server)


def test_your_own_email_is_a_silent_no_op():
    """Not even a 400: a validation error on your own address tells an attacker
    which email is theirs versus merely unknown."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            me = _parent(client, "ct-self", "Sam Self")
            _give_identity(server, "ct-self", "sam.self@example.com")

            r = client.post("/circle/contacts",
                            json={"email": "sam.self@example.com"}, headers=me)
            assert r.status_code == 200 and r.json() == {"status": "sent"}
            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests WHERE from_user_id = ?",
                ["ct-self"],
            ).fetchone()[0] == 0, "you sent yourself a Circle request"
    finally:
        _reconnect_shared_storage(server)


def test_duplicate_contacts_for_the_same_pair_does_not_stack_pendings():
    """The duplicate guard is in CODE (DuckDB has no partial unique index), so
    it needs a test — a stacked pending would show the recipient the same ask
    twice and leave orphan rows behind an accept."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-dup-asker", "Ana Asker")
            _parent(client, "ct-dup-target", "Ben Target")
            _give_identity(server, "ct-dup-target", "dup.target@example.com")

            for _ in range(3):
                r = client.post("/circle/contacts",
                                json={"email": "dup.target@example.com"}, headers=asker)
                assert r.status_code == 200 and r.json() == {"status": "sent"}

            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests "
                "WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending'",
                ["ct-dup-asker", "ct-dup-target"],
            ).fetchone()[0] == 1, "re-asking stacked a second pending request"
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# A pending request grants NOTHING
# --------------------------------------------------------------------------- #


def test_a_pending_request_grants_no_access_at_all():
    """The consent property. Between "sent" and "accepted" the requester must be
    exactly as powerless as a stranger: not in `circle_peer_ids`, and 404 on
    every route of the target's conversation."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-pend-asker", "Ana Asker")
            target = _parent(client, "ct-pend-target", "Ben Target")
            _give_identity(server, "ct-pend-target", "pend.target@example.com")

            # The target has a private thread of their own.
            conv = client.post("/circle/conversations",
                               json={"title": "Ben's private thread"},
                               headers=target).json()
            conv_id = conv["id"]

            assert client.post("/circle/contacts",
                               json={"email": "pend.target@example.com"},
                               headers=asker).status_code == 200

            storage = server.storage_backend
            assert "ct-pend-target" not in storage.circle_peer_ids("ct-pend-asker"), (
                "a PENDING request put the target in the requester's Circle"
            )
            assert "ct-pend-asker" not in storage.circle_peer_ids("ct-pend-target")

            # Listing shows nothing of the target's.
            listed = client.get("/circle/conversations", headers=asker).json()
            assert [c["id"] for c in listed["conversations"]] == []

            # Reading and posting are 404, not 403 (a 403 confirms it exists).
            assert client.get(f"/circle/conversations/{conv_id}",
                              headers=asker).status_code == 404
            assert client.post(f"/circle/conversations/{conv_id}/messages",
                               json={"body": "hello"}, headers=asker).status_code == 404
            assert client.post(f"/circle/conversations/{conv_id}/read",
                               headers=asker).status_code == 404
    finally:
        _reconnect_shared_storage(server)


def test_the_recipient_sees_the_pending_request_in_their_inbox():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-inbox-asker", "Ana Asker")
            target = _parent(client, "ct-inbox-target", "Ben Target")
            _give_identity(server, "ct-inbox-target", "inbox.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "inbox.target@example.com"}, headers=asker)

            inbox = client.get("/circle/requests", headers=target)
            assert inbox.status_code == 200, inbox.text
            requests = inbox.json()["requests"]
            assert len(requests) == 1
            row = requests[0]
            assert row["from_user_id"] == "ct-inbox-asker"
            assert row["from_name"] == "Ana Asker"
            assert row["initials"] == "AA"
            assert row["status"] == "pending"
            assert row["id"] and row["created_at"]

            # The REQUESTER's own inbox is empty: /requests is inbound only.
            assert client.get("/circle/requests", headers=asker).json()["requests"] == []
    finally:
        _reconnect_shared_storage(server)


def test_the_requester_gets_a_local_roster_row_for_the_pending_contact():
    """The contacts list has to show who you asked. The row exists but carries
    NO member_user_id, so it is an address-book entry and not a link."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-roster-asker", "Ana Asker")
            _parent(client, "ct-roster-target", "Ben Target")
            _give_identity(server, "ct-roster-target", "roster.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "roster.target@example.com",
                              "display_name": "Ben the Nanny"},
                        headers=asker)

            members = client.get("/household/members", headers=asker).json()["members"]
            assert len(members) == 1
            assert members[0]["display_name"] == "Ben the Nanny"
            assert members[0]["member_user_id"] is None, (
                "the pending roster row was pre-linked — a pending request must "
                "not write member_user_id"
            )
            assert members[0]["linked"] is False
            assert members[0]["in_circle"] is False
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# Accept / decline
# --------------------------------------------------------------------------- #


def test_accept_establishes_the_link_in_both_directions():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-acc-asker", "Ana Asker")
            target = _parent(client, "ct-acc-target", "Ben Target")
            _give_identity(server, "ct-acc-target", "acc.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "acc.target@example.com"}, headers=asker)
            request_id = client.get("/circle/requests",
                                    headers=target).json()["requests"][0]["id"]

            r = client.post(f"/circle/requests/{request_id}/accept", headers=target)
            assert r.status_code == 200, r.text
            assert r.json() == {"ok": True, "status": "accepted",
                               "from_user_id": "ct-acc-asker"}

            storage = server.storage_backend
            assert "ct-acc-target" in storage.circle_peer_ids("ct-acc-asker")
            assert "ct-acc-asker" in storage.circle_peer_ids("ct-acc-target"), (
                "the link is one-sided — circle_peer_ids requires BOTH directions"
            )
            # And it is usable: the now-peer can be added to a conversation.
            members = client.get("/household/members", headers=asker).json()["members"]
            peer_member = next(m for m in members
                               if m["member_user_id"] == "ct-acc-target")
            assert peer_member["in_circle"] is True
            conv = client.post("/circle/conversations",
                               json={"title": "Pickup plan",
                                     "member_ids": [peer_member["id"]]},
                               headers=asker)
            assert conv.status_code == 200, conv.text
            assert client.get(f"/circle/conversations/{conv.json()['id']}",
                              headers=target).status_code == 200

            # The request is answered, so it leaves the inbox.
            assert client.get("/circle/requests", headers=target).json()["requests"] == []
    finally:
        _reconnect_shared_storage(server)


def test_decline_establishes_nothing():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-dec-asker", "Ana Asker")
            target = _parent(client, "ct-dec-target", "Ben Target")
            _give_identity(server, "ct-dec-target", "dec.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "dec.target@example.com"}, headers=asker)
            request_id = client.get("/circle/requests",
                                    headers=target).json()["requests"][0]["id"]

            r = client.post(f"/circle/requests/{request_id}/decline", headers=target)
            assert r.status_code == 200, r.text
            assert r.json()["status"] == "declined"

            storage = server.storage_backend
            assert storage.circle_peer_ids("ct-dec-asker") == []
            assert storage.circle_peer_ids("ct-dec-target") == []
            assert client.get("/circle/requests", headers=target).json()["requests"] == []

            # Answering twice is a conflict, not a second silent write.
            assert client.post(f"/circle/requests/{request_id}/accept",
                               headers=target).status_code == 409
    finally:
        _reconnect_shared_storage(server)


def test_a_third_party_cannot_answer_someone_elses_request():
    """404 rather than 403 on both verbs — the same posture as
    `_conversation_or_404`: the existence check layers before the ownership one,
    so a stranger cannot distinguish "no such request" from "not yours"."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-3p-asker", "Ana Asker")
            target = _parent(client, "ct-3p-target", "Ben Target")
            stranger = _parent(client, "ct-3p-stranger", "Eve Stranger")
            _give_identity(server, "ct-3p-target", "third.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "third.target@example.com"}, headers=asker)
            request_id = client.get("/circle/requests",
                                    headers=target).json()["requests"][0]["id"]

            for headers, who in ((stranger, "a stranger"), (asker, "the requester")):
                assert client.post(f"/circle/requests/{request_id}/accept",
                                   headers=headers).status_code == 404, (
                    f"{who} was able to accept a request addressed to someone else"
                )
                assert client.post(f"/circle/requests/{request_id}/decline",
                                   headers=headers).status_code == 404

            # An id that does not exist looks exactly the same.
            assert client.post("/circle/requests/cr-nope/accept",
                               headers=stranger).status_code == 404

            # Still pending and still nobody's peer.
            assert len(client.get("/circle/requests",
                                  headers=target).json()["requests"]) == 1
            assert server.storage_backend.circle_peer_ids("ct-3p-asker") == []
    finally:
        _reconnect_shared_storage(server)


def test_accept_survives_the_requester_deleting_the_roster_row_first():
    """A real race: the requester deletes the pending contact while waiting.
    Accept must re-create the row rather than bind a dangling id (or crash)."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-race-asker", "Ana Asker")
            target = _parent(client, "ct-race-target", "Ben Target")
            _give_identity(server, "ct-race-target", "race.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "race.target@example.com"}, headers=asker)
            member_id = client.get("/household/members",
                                   headers=asker).json()["members"][0]["id"]
            assert client.delete(f"/household/members/{member_id}",
                                 headers=asker).status_code == 200

            request_id = client.get("/circle/requests",
                                    headers=target).json()["requests"][0]["id"]
            assert client.post(f"/circle/requests/{request_id}/accept",
                               headers=target).status_code == 200

            storage = server.storage_backend
            assert "ct-race-target" in storage.circle_peer_ids("ct-race-asker")
            assert "ct-race-asker" in storage.circle_peer_ids("ct-race-target")
    finally:
        _reconnect_shared_storage(server)


def test_asking_someone_who_is_already_a_peer_is_a_silent_no_op():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-peer-asker", "Ana Asker")
            target = _parent(client, "ct-peer-target", "Ben Target")
            _give_identity(server, "ct-peer-target", "peer.target@example.com")

            client.post("/circle/contacts",
                        json={"email": "peer.target@example.com"}, headers=asker)
            request_id = client.get("/circle/requests",
                                    headers=target).json()["requests"][0]["id"]
            client.post(f"/circle/requests/{request_id}/accept", headers=target)

            r = client.post("/circle/contacts",
                            json={"email": "peer.target@example.com"}, headers=asker)
            assert r.status_code == 200 and r.json() == {"status": "sent"}
            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests WHERE from_user_id = ?",
                ["ct-peer-asker"],
            ).fetchone()[0] == 1, "asking an existing peer created a second request"
    finally:
        _reconnect_shared_storage(server)


def test_the_invite_claim_and_the_request_accept_share_one_binding():
    """Both doors into the mutual link go through `_bind_mutual_link`. If a
    future edit copies that block instead, this asserts the two paths still
    produce the SAME shape (both sides linked, reciprocal row present)."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            inviter = _parent(client, "ct-both-inviter", "Ana Inviter")
            claimer = _parent(client, "ct-both-claimer", "Ben Claimer")
            requester = _parent(client, "ct-both-requester", "Cara Requester")
            accepter = _parent(client, "ct-both-accepter", "Dan Accepter")
            _give_identity(server, "ct-both-accepter", "both.accepter@example.com")

            token = client.post("/circle/invites", json={}, headers=inviter).json()["token"]
            assert client.post(f"/circle/invites/{token}/claim",
                               headers=claimer).status_code == 200

            client.post("/circle/contacts",
                        json={"email": "both.accepter@example.com"}, headers=requester)
            request_id = client.get("/circle/requests",
                                    headers=accepter).json()["requests"][0]["id"]
            assert client.post(f"/circle/requests/{request_id}/accept",
                               headers=accepter).status_code == 200

            storage = server.storage_backend
            for a, b in (("ct-both-inviter", "ct-both-claimer"),
                         ("ct-both-requester", "ct-both-accepter")):
                assert b in storage.circle_peer_ids(a), f"{a} -> {b} not linked"
                assert a in storage.circle_peer_ids(b), f"{b} -> {a} not linked"
                assert storage.find_household_member_by_account(b, a) is not None, (
                    f"{b} has no reciprocal roster row for {a}"
                )
    finally:
        _reconnect_shared_storage(server)


def test_deleting_an_account_takes_its_requests_in_both_directions():
    """Deletes cascade (CLAUDE.md). A surviving row would point a live inbox at
    a dead user_id, and a re-issued id would inherit an ask it never made."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-del-asker", "Ana Asker")
            target = _parent(client, "ct-del-target", "Ben Target")
            _give_identity(server, "ct-del-target", "del.target@example.com")
            _give_identity(server, "ct-del-asker", "del.asker@example.com")

            client.post("/circle/contacts",
                        json={"email": "del.target@example.com"}, headers=asker)
            client.post("/circle/contacts",
                        json={"email": "del.asker@example.com"}, headers=target)
            # Scoped to this pair: the suite shares one db file, so a global
            # count would fold in every other test's rows.
            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests "
                "WHERE from_user_id IN (?, ?) OR to_user_id IN (?, ?)",
                ["ct-del-asker", "ct-del-target", "ct-del-asker", "ct-del-target"],
            ).fetchone()[0] == 2

            server.storage_backend.delete_family(user_id="ct-del-asker", actor="test")
            assert server.storage_backend._con.execute(
                "SELECT count(*) FROM circle_requests "
                "WHERE from_user_id = ? OR to_user_id = ?",
                ["ct-del-asker", "ct-del-asker"],
            ).fetchone()[0] == 0, "requests outlived the deleted account"
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# Rate limits — the contacts lookup is the probe surface
# --------------------------------------------------------------------------- #


def test_the_contacts_lookup_is_rate_limited():
    """Without a bucket, an attacker can walk an email list at request speed.
    The identical-response property only buys anonymity if the probe is also
    expensive, so the route draws on the `config` bucket."""
    from fastapi.testclient import TestClient
    import app.server as server
    from app.rate_limit import CONFIG_RATE_PER_MIN

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            asker = _parent(client, "ct-rl-asker", "Ana Asker")

            statuses = [
                client.post("/circle/contacts",
                            json={"email": f"probe{i}@example.com"},
                            headers=asker).status_code
                for i in range(CONFIG_RATE_PER_MIN + 5)
            ]
            assert 429 in statuses, (
                "POST /circle/contacts served an unbounded number of email probes"
            )
    finally:
        _reconnect_shared_storage(server)
