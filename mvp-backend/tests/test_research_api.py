"""
End-to-end HTTP test of the discovery API (app/research/router.py) + the
background worker, driven through FastAPI's TestClient. The discovery function
is faked so the real routes, auth, rate-limit, enqueue, worker thread, and
storage all run with NO LLM / network cost.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH *before* importing app.server
(which builds storage at module load), so this never touches the dev DB. Both
scenarios run inside a single TestClient context: each context exit runs
lifespan shutdown (which closes the shared storage singleton), so we only enter
it once.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Point storage at a temp DB before importing the server module.
os.environ["MVP_DUCKDB_PATH"] = str(Path(tempfile.mkdtemp()) / "research_api.duckdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.research.graph as research_graph  # noqa: E402
import app.server as server  # noqa: E402


def _fake_discover(**kwargs):
    return [
        {"name": "Camp Tule", "kid_name": "Ceiba", "category": "camp",
         "fit_score": 0.8, "signup_url": "https://example.org/tule"},
        {"name": "Little Monsters", "kid_name": "Ceiba", "category": "camp", "fit_score": 0.6},
    ]


# Bind the fake at module level so the lifespan-started worker uses it (it binds
# discover_fn at startup, before any function-scoped monkeypatch could apply).
research_graph.discover_activities = _fake_discover


def _issue_token(client, user_id: str) -> str:
    resp = client.post("/auth/issue-token", json={"user_id": user_id})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def test_research_api_end_to_end_and_auth():
    with TestClient(server.app) as client:
        user_id = "nl-harness-research-api-test"
        token = _issue_token(client, user_id)
        auth = {"Authorization": f"Bearer {token}"}

        # ── auth gating ──────────────────────────────────────────────
        assert client.post("/research/runs", json={"user_id": user_id}).status_code == 401
        cross = client.post(
            "/research/runs", json={"user_id": "a-different-user"}, headers=auth
        )
        assert cross.status_code == 403

        # ── trigger a run ────────────────────────────────────────────
        resp = client.post("/research/runs", json={"user_id": user_id}, headers=auth)
        assert resp.status_code == 200, resp.text
        run_id = resp.json()["run_id"]
        assert resp.json()["status"] == "queued"

        # ── poll until the worker finishes (fake discovery is instant) ─
        status = None
        for _ in range(50):
            r = client.get(f"/research/runs/{run_id}", headers=auth)
            assert r.status_code == 200
            status = r.json()["status"]
            if status in ("done", "failed"):
                break
            time.sleep(0.1)
        assert status == "done", f"run ended as {status}"

        # ── candidates persisted + ranked by fit_score ───────────────
        r = client.get(f"/research/runs/{run_id}/candidates", headers=auth)
        assert r.status_code == 200
        assert [c["name"] for c in r.json()["candidates"]] == ["Camp Tule", "Little Monsters"]

        # ── run appears in the user's list ───────────────────────────
        r = client.get("/research/runs", headers=auth)
        assert any(run["id"] == run_id for run in r.json()["runs"])

        # ── another user's bearer can't read this run ────────────────
        # 404, not 403: a non-owner must not even learn the run_id exists
        # (authorize_user_match resource=True).
        other_token = _issue_token(client, "nl-harness-other-user")
        r = client.get(
            f"/research/runs/{run_id}", headers={"Authorization": f"Bearer {other_token}"}
        )
        assert r.status_code == 404
