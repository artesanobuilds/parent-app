"""Saved items — the Saved tab (2026-07-19).

The invariants:
  • Server-side denormalization: content saves snapshot title/snippet/tags from
    the content tables (client can't spoof; snapshot survives CMS edit/delete).
  • coach_reply carries its body from the client — the snapshot is the ONLY
    copy (LangGraph memory is ephemeral) — and body is required.
  • Soft delete + re-save: unsave keeps the row (signal); re-saving revives it
    and bumps save_count. No unique-constraint trap.
  • /saved/refs returns ACTIVE refs only (the N+1 killer for card surfaces).
  • The merged list projects the Plan shortlist (origin 'plan') WITHOUT
    materializing it into saved_items.
  • saved_signal digests tags + titles for the coach prompt (read-time only).
  • delete_family removes saved_items.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "saved.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def test_saved_lifecycle():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            storage = server.storage_backend
            storage.create_article({
                "id": "art-save-1", "category": "cat-sleep", "title": "Bedtime Wars",
                "subtitle": "Ending the 9pm standoff", "emoji": "", "read_time": "",
                "summary": "", "tags": ["sleep", "toddler"], "content": "long body",
            })

            uid = "saved-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # ── auth gates ───────────────────────────────────────────
            assert client.get("/saved").status_code == 401
            assert client.post("/saved", json={"item_type": "article", "item_ref": "x"}).status_code == 401

            # ── article save: server denormalizes the snapshot ───────
            r = client.post("/saved", json={
                "item_type": "article", "item_ref": "art-save-1",
                "context": {"surface": "library"},
            }, headers=auth)
            assert r.status_code == 200, r.text
            item = r.json()
            assert item["title"] == "Bedtime Wars"
            assert item["snippet"] == "Ending the 9pm standoff"
            assert set(item["topic_tags"]) == {"sleep", "toddler", "cat-sleep"}
            # unknown content 404s; unknown type 400s
            assert client.post("/saved", json={"item_type": "article", "item_ref": "nope"},
                               headers=auth).status_code == 404
            assert client.post("/saved", json={"item_type": "activity", "item_ref": "a"},
                               headers=auth).status_code == 400

            # ── coach_reply: body required, snapshot stored ──────────
            assert client.post("/saved", json={
                "item_type": "coach_reply", "item_ref": "msg-uuid-1",
            }, headers=auth).status_code == 400
            r = client.post("/saved", json={
                "item_type": "coach_reply", "item_ref": "msg-uuid-1",
                "body": "Try naming the feeling before the fix — it lands better.",
                "kid_name": "Nia",
            }, headers=auth)
            assert r.status_code == 200
            assert r.json()["body"].startswith("Try naming")
            assert r.json()["kid_name"] == "Nia"

            # ── refs ─────────────────────────────────────────────────
            refs = client.get("/saved/refs?item_type=article", headers=auth).json()["refs"]
            assert refs == ["art-save-1"]
            # The retired board can no longer be SAVED (its tables are gone),
            # but DELETE still accepts the type so an old row can be cleared.
            assert client.post("/saved", json={"item_type": "community_post",
                                               "item_ref": "post-save-1"},
                               headers=auth).status_code == 400

            # ── snapshot survives content deletion ───────────────────
            storage.delete_article("art-save-1")
            listed = client.get("/saved", headers=auth).json()["items"]
            art = next(i for i in listed if i["item_ref"] == "art-save-1")
            assert art["title"] == "Bedtime Wars"  # denormalized copy lives on

            # ── unsave (soft) → refs shrink → re-save bumps count ────
            # On coach_reply: art-save-1's row was deleted just above, so
            # re-saving it would (correctly) 404 on the content lookup.
            r = client.delete("/saved?item_type=coach_reply&item_ref=msg-uuid-1",
                              headers=auth)
            assert r.json()["unsaved"] is True
            assert client.get("/saved/refs?item_type=coach_reply",
                              headers=auth).json()["refs"] == []
            r = client.post("/saved", json={
                "item_type": "coach_reply", "item_ref": "msg-uuid-1",
                "body": "Try naming the feeling before the fix — it lands better.",
            }, headers=auth)
            assert r.json()["save_count"] == 2  # revived, not duplicated
            # double-unsave is a no-op False
            client.delete("/saved?item_type=coach_reply&item_ref=msg-uuid-1", headers=auth)
            assert client.delete("/saved?item_type=coach_reply&item_ref=msg-uuid-1",
                                 headers=auth).json()["unsaved"] is False

            # ── merged Plan projection (never materialized) ──────────
            storage.track_activity(
                uid, name="Robotics Camp", status="exploring", activity_type="camp",
            )
            listed = client.get("/saved", headers=auth).json()["items"]
            plan_rows = [i for i in listed if i.get("origin") == "plan"]
            assert len(plan_rows) == 1 and plan_rows[0]["title"] == "Robotics Camp"
            assert storage.saved_refs(uid, "activity") == []  # not in saved_items

            # ── the coach signal digest ──────────────────────────────
            signal = storage.saved_signal(uid)
            assert ("sleep", 1) in signal["top_tags"]
            assert any("Bedtime Wars" in t for t in signal["recent_titles"])

            # ── delete_family removes saved_items ────────────────────
            r = client.delete(f"/family/{uid}", headers=auth)
            assert r.status_code == 200
            assert r.json()["deleted"].get("saved_items", 0) >= 2
    finally:
        _reconnect_shared_storage(server)
