"""
End-to-end HTTP test of the Chief-of-Staff API (app/cos/router.py), driven
through FastAPI's TestClient. The chat agent is faked so the SSE path runs with
NO LLM / network cost; the CRUD + plan-summary paths exercise the real routes,
auth, and storage.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH *before* importing app.server
(which builds storage at module load), so this never touches the dev DB. Every
assertion runs inside a SINGLE TestClient context: each context exit runs
lifespan shutdown (which closes the shared storage singleton), so we only enter
it once.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Point storage at a temp DB before importing the server module.
os.environ["MVP_DUCKDB_PATH"] = str(Path(tempfile.mkdtemp()) / "cos_api.duckdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.cos.router as cos_router  # noqa: E402
import app.server as server  # noqa: E402


# --------------------------------------------------------------------------- #
# Fake chat agent (mirrors tests/agents/test_sse_envelope.py)
# --------------------------------------------------------------------------- #


class _FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


async def _fake_astream_events(*args, **kwargs):
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk("On it")}}
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk(" — tracked.")}}
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk("")}}  # skipped


class _FakeAgent:
    async def aget_state(self, config):
        from types import SimpleNamespace
        return SimpleNamespace(values={"messages": []})

    def astream_events(self, *args, **kwargs):
        return _fake_astream_events(*args, **kwargs)


def _issue_token(client, user_id: str) -> str:
    resp = client.post("/auth/issue-token", json={"user_id": user_id})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def _parse_sse(text: str):
    events = []
    for raw in text.split("\n\n"):
        raw = raw.strip()
        if not raw:
            continue
        body = raw[len("data: "):]
        if body == "[DONE]":
            events.append(body)
        else:
            import json

            events.append(json.loads(body))
    return events


def _reconnect_shared_storage():
    """``app.server`` builds ONE storage singleton at module import, shared across
    every test module that imports it. Our TestClient's lifespan-exit closes that
    connection — which would poison a later test module's TestClient. Rebuild the
    singleton against the same DB file so the shared connection is live again.
    (This is a cross-module test-isolation concern, not production behavior.)
    """
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def test_cos_api_end_to_end_and_auth(monkeypatch):
    # The router imported get_cos_agent into its own namespace; patch that name.
    monkeypatch.setattr(cos_router, "get_cos_agent", lambda user_id: _FakeAgent())

    try:
        _run_cos_assertions()
    finally:
        _reconnect_shared_storage()


def _run_cos_assertions():
    with TestClient(server.app) as client:
        user_id = "nl-harness-cos-api-test"
        token = _issue_token(client, user_id)
        auth = {"Authorization": f"Bearer {token}"}

        # ── auth gating ──────────────────────────────────────────────
        assert (
            client.post(
                "/cos/activities/track", json={"user_id": user_id, "name": "X"}
            ).status_code
            == 401
        )
        cross = client.post(
            "/cos/activities/track",
            json={"user_id": "a-different-user", "name": "X"},
            headers=auth,
        )
        assert cross.status_code == 403

        # ── chat: SSE envelope + persistence ─────────────────────────
        with client.stream(
            "POST",
            "/cos/chat",
            json={"user_id": user_id, "message": "track soccer camp"},
            headers=auth,
        ) as resp:
            assert resp.status_code == 200
            body = "".join(resp.iter_text())
        events = _parse_sse(body)
        tokens = [e for e in events if isinstance(e, dict) and e.get("type") == "token"]
        assert [t["content"] for t in tokens] == ["On it", " — tracked."]
        assert events[-1] == "[DONE]"

        msgs = client.get("/cos/messages", headers=auth).json()["messages"]
        assert [(m["role"], m["content"]) for m in msgs] == [
            ("user", "track soccer camp"),
            ("assistant", "On it — tracked."),
        ]

        # ── tracked activities: create → list → confirm ──────────────
        r = client.post(
            "/cos/activities/track",
            json={
                "user_id": user_id,
                "name": "Soccer Camp",
                "kid_name": "Ceiba",
                "status": "interested",
                "price_amount": 250.0,
                "price_status": "confirmed",
            },
            headers=auth,
        )
        assert r.status_code == 200, r.text
        activity_id = r.json()["id"]

        listed = client.get("/cos/activities", headers=auth).json()["activities"]
        assert any(a["id"] == activity_id for a in listed)

        r = client.patch(
            f"/cos/activities/{activity_id}",
            json={"user_id": user_id, "status": "confirmed"},
            headers=auth,
        )
        assert r.status_code == 200, r.text
        assert r.json()["activity"]["status"] == "confirmed"

        # ── calendar: create → list (covers Ceiba's week) ────────────
        r = client.post(
            "/cos/calendar",
            json={
                "user_id": user_id,
                "title": "Soccer Camp",
                "kid_name": "Ceiba",
                "week_start": "2026-07-06",
                "kind": "camp",
                "activity_id": activity_id,
            },
            headers=auth,
        )
        assert r.status_code == 200, r.text
        entry_id = r.json()["id"]
        cal = client.get("/cos/calendar", headers=auth).json()["entries"]
        assert any(e["id"] == entry_id for e in cal)

        # ── todos: create → complete ─────────────────────────────────
        r = client.post(
            "/cos/todos",
            json={"user_id": user_id, "title": "Pay Soccer Camp deposit"},
            headers=auth,
        )
        assert r.status_code == 200, r.text
        todo_id = r.json()["id"]
        r = client.patch(
            f"/cos/todos/{todo_id}",
            json={"user_id": user_id, "status": "done"},
            headers=auth,
        )
        assert r.status_code == 200, r.text
        done = client.get("/cos/todos?status=done", headers=auth).json()["todos"]
        assert any(t["id"] == todo_id for t in done)

        # ── caregivers ───────────────────────────────────────────────
        r = client.post(
            "/cos/caregivers",
            json={"user_id": user_id, "name": "Grandma", "role": "grandparent"},
            headers=auth,
        )
        assert r.status_code == 200, r.text
        assert client.get("/cos/caregivers", headers=auth).json()["caregivers"]

        # ── logistics with an explicit coverage gap ──────────────────
        r = client.post(
            "/cos/logistics",
            json={
                "user_id": user_id,
                "task": "pickup",
                "kid_name": "Ceiba",
                "week_start": "2026-07-06",
                "status": "gap",
            },
            headers=auth,
        )
        assert r.status_code == 200, r.text

        # ── plan summary: shape + the gap surfaces ───────────────────
        summary = client.get("/cos/plan/summary", headers=auth).json()
        for key in (
            "cost",
            "conflicts",
            "coverage_gaps",
            "uncovered_weeks",
            "pending_eligibility",
        ):
            assert key in summary, f"missing key {key}"
        assert summary["cost"]["confirmed_total"] == 250.0
        assert any(g["task"] == "pickup" for g in summary["coverage_gaps"])

        # ── cross-user can't read or patch this user's data ──────────
        other = _issue_token(client, "nl-harness-cos-other")
        other_auth = {"Authorization": f"Bearer {other}"}
        # GETs derive user from the token, so the other user simply sees nothing.
        assert (
            client.get("/cos/activities", headers=other_auth).json()["activities"] == []
        )
        # A cross-user PATCH (claimed != authenticated) is 403.
        r = client.patch(
            f"/cos/activities/{activity_id}",
            json={"user_id": user_id, "status": "declined"},
            headers=other_auth,
        )
        assert r.status_code == 403
