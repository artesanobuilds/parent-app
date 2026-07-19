"""Parent-to-parent direct messages (2026-07-19).

The invariants that make the simple v1 safe:
  • ONE conversation per pair — A→B and B→A land in the same canonical row.
  • Participant guard: non-participants get 404 (never 403 — don't confirm
    existence). test_bola_sweep introspects the {conversation_id} paths too.
  • Block: either side's flag 403s sends; unblock restores.
  • Unread math: peer messages after MY read stamp; my own sends never count.
  • Directory: resolvable names only, self excluded.
  • delete_family removes BOTH sides' threads (my messages are my data).
  • Community author user_ids: visible to signed-in readers (DM peer handle),
    STRIPPED for anonymous callers — the recon found them publicly leaked.
  • Report emails the founder; a push fires at the peer on send.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "dm.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _parent(client, user_id, name):
    tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
    auth = {"Authorization": f"Bearer {tok}"}
    client.patch("/profile", json={"name": name}, headers=auth)
    return auth


def test_dm_full_lifecycle(monkeypatch):
    from fastapi.testclient import TestClient
    import app.server as server

    pushes, emails = [], []
    monkeypatch.setattr("app.push.send_push",
                        lambda **kw: pushes.append(kw) or "sent")
    monkeypatch.setattr("app.email_smtp.send_email",
                        lambda subject, body, to=None: emails.append((subject, body)) or True)

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            alice = _parent(client, "dm-alice", "Alice Ash")
            bob = _parent(client, "dm-bob", "Bob Birch")
            eve = _parent(client, "dm-eve", "Eve Elder")

            # ── directory: names resolved, self excluded ─────────────
            members = client.get("/dm/members", headers=alice).json()["members"]
            ids = {m["user_id"] for m in members}
            assert "dm-bob" in ids and "dm-eve" in ids and "dm-alice" not in ids
            bob_entry = next(m for m in members if m["user_id"] == "dm-bob")
            assert bob_entry["display_name"] == "Bob Birch"
            assert bob_entry["initials"] == "BB"

            # ── canonical pair: A→B and B→A are ONE conversation ─────
            c1 = client.post("/dm/conversations", json={"peer_user_id": "dm-bob"},
                             headers=alice).json()
            c2 = client.post("/dm/conversations", json={"peer_user_id": "dm-alice"},
                             headers=bob).json()
            assert c1["id"] == c2["id"]
            conv_id = c1["id"]
            assert c1["peer_name"] == "Bob Birch" and c2["peer_name"] == "Alice Ash"
            # self + unknown peer rejected
            assert client.post("/dm/conversations", json={"peer_user_id": "dm-alice"},
                               headers=alice).status_code == 400
            assert client.post("/dm/conversations", json={"peer_user_id": "nobody-here"},
                               headers=alice).status_code == 404

            # ── send + push + preview denorm ─────────────────────────
            r = client.post(f"/dm/conversations/{conv_id}/messages",
                            json={"body": "Camp carpool Thursday?"}, headers=alice)
            assert r.status_code == 200, r.text
            assert pushes and pushes[-1]["user_id"] == "dm-bob"
            assert pushes[-1]["title"] == "Alice Ash"
            assert client.post(f"/dm/conversations/{conv_id}/messages",
                               json={"body": "  "}, headers=alice).status_code == 400
            assert client.post(f"/dm/conversations/{conv_id}/messages",
                               json={"body": "x" * 2001}, headers=alice).status_code == 400

            # ── unread math ──────────────────────────────────────────
            inbox_bob = client.get("/dm/conversations", headers=bob).json()
            assert inbox_bob["total_unread"] == 1
            assert inbox_bob["conversations"][0]["last_message_preview"] == "Camp carpool Thursday?"
            inbox_alice = client.get("/dm/conversations", headers=alice).json()
            assert inbox_alice["total_unread"] == 0  # my own send is never unread
            client.post(f"/dm/conversations/{conv_id}/read", headers=bob)
            assert client.get("/dm/conversations", headers=bob).json()["total_unread"] == 0

            # ── participant guard: eve sees nothing, everywhere ──────
            for method, path in [
                ("get", f"/dm/conversations/{conv_id}/messages"),
                ("post", f"/dm/conversations/{conv_id}/read"),
                ("post", f"/dm/conversations/{conv_id}/block"),
                ("post", f"/dm/conversations/{conv_id}/report"),
            ]:
                resp = getattr(client, method)(
                    path, **({"json": {}} if method == "post" else {}), headers=eve
                )
                assert resp.status_code == 404, f"{path}: {resp.status_code}"
            assert client.get(f"/dm/conversations/{conv_id}/messages").status_code == 401

            # ── block semantics ──────────────────────────────────────
            client.post(f"/dm/conversations/{conv_id}/block", headers=bob)
            assert client.post(f"/dm/conversations/{conv_id}/messages",
                               json={"body": "hello?"}, headers=alice).status_code == 403
            assert client.post(f"/dm/conversations/{conv_id}/messages",
                               json={"body": "me neither"}, headers=bob).status_code == 403
            client.post(f"/dm/conversations/{conv_id}/unblock", headers=bob)
            assert client.post(f"/dm/conversations/{conv_id}/messages",
                               json={"body": "Sure — Thursday works"},
                               headers=bob).status_code == 200

            # ── pagination cursor ────────────────────────────────────
            msgs = client.get(f"/dm/conversations/{conv_id}/messages?limit=1",
                              headers=alice).json()["messages"]
            assert len(msgs) == 1 and msgs[0]["body"] == "Sure — Thursday works"
            older = client.get(
                f"/dm/conversations/{conv_id}/messages?limit=5&before={msgs[0]['created_at']}",
                headers=alice).json()["messages"]
            assert older and older[0]["body"] == "Camp carpool Thursday?"

            # ── report emails the founder with context ───────────────
            r = client.post(f"/dm/conversations/{conv_id}/report",
                            json={"note": "test report"}, headers=alice)
            assert r.status_code == 200
            assert emails and "DM report" in emails[-1][0]
            assert "Camp carpool Thursday?" in emails[-1][1]

            # ── delete_family removes BOTH sides' threads ────────────
            r = client.delete("/family/dm-alice", headers=alice)
            assert r.status_code == 200
            assert r.json()["deleted"].get("dm_conversations") == 1
            assert client.get("/dm/conversations", headers=bob).json()["conversations"] == []
    finally:
        _reconnect_shared_storage(server)


def test_community_author_ids_gated_on_auth():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            carol = _parent(client, "dm-carol", "Carol Cedar")
            post = client.post(
                "/content/community/new",
                json={"user_id": "dm-carol", "author_name": "Carol Cedar",
                      "category": "cat-any", "title": "Hi", "preview": "hello"},
                headers=carol,
            ).json()
            client.post(
                f"/content/community/{post['id']}/replies",
                json={"user_id": "dm-carol", "author_name": "Carol Cedar", "body": "me too"},
                headers=carol,
            )

            # Signed-in readers get author user_ids (the DM peer handle)…
            listed = client.get("/content/community", headers=carol).json()
            mine = next(p for p in listed if p["id"] == post["id"])
            assert mine.get("user_id") == "dm-carol"
            detail = client.get(f"/content/community/{post['id']}", headers=carol).json()
            assert detail.get("user_id") == "dm-carol"
            assert detail["replies"][0].get("user_id") == "dm-carol"

            # …anonymous readers do NOT (user_id is the auth principal).
            for payload in (
                client.get("/content/community").json(),
                [client.get(f"/content/community/{post['id']}").json()],
                client.get(f"/content/community/{post['id']}/replies").json(),
            ):
                for item in payload:
                    assert "user_id" not in item, item
                    for reply in item.get("replies", []) if isinstance(item, dict) else []:
                        assert "user_id" not in reply
    finally:
        _reconnect_shared_storage(server)
