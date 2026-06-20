"""
Tests for Phase 3 multimodal ingestion.

Two layers, both hermetic (tempfile DuckDB, no network):
  * storage CRUD for ``ingest_artifacts`` + the deterministic Stage-2
    ``materialize()`` (eligibility -> pending, to-dos, calendar);
  * the HTTP API (``/ingest/text``, ``/ingest/image``, ``/cos/draft-email``)
    via FastAPI's TestClient with the LLM calls faked, exercising auth gating
    and the real routes/storage.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH *before* importing app.server
(which builds storage at module load). Mirrors tests/test_cos_api.py.
"""
from __future__ import annotations

import base64
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.ingest.extract import (  # noqa: E402
    Contact,
    ExtractedActivity,
    Link,
    materialize,
)


# --------------------------------------------------------------------------- #
# Layer 1: storage CRUD + Stage-2 materialization (hermetic)
# --------------------------------------------------------------------------- #


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "ingest.duckdb")


def test_ingest_artifact_crud_and_isolation(store):
    aid = store.insert_ingest_artifact(
        "u1", source="paste", media_type="text", raw_text="hi", subject="Camp HBG"
    )
    got = store.get_ingest_artifact(aid, "u1")
    assert got["source"] == "paste"
    assert got["extract_status"] == "pending"
    assert got["raw_text"] == "hi"
    assert got["extracted"] is None

    store.update_ingest_extraction(
        aid,
        extracted_json={"provider": "Camp HBG"},
        links_json=[{"label": "Reg", "url": "http://x"}],
        extract_status="extracted",
    )
    got = store.get_ingest_artifact(aid, "u1")
    assert got["extract_status"] == "extracted"
    assert got["extracted"] == {"provider": "Camp HBG"}
    assert got["links"] == [{"label": "Reg", "url": "http://x"}]

    # Cross-user isolation: another user cannot read it.
    assert store.get_ingest_artifact(aid, "other") is None
    assert store.list_ingest_artifacts("other") == []

    # Status filter.
    assert len(store.list_ingest_artifacts("u1", status="extracted")) == 1
    assert store.list_ingest_artifacts("u1", status="failed") == []


def test_materialize_under_age_goes_pending_with_confirm_todo(store):
    """The grounding-artifact rule: a kid below the activity's age floor must
    land PENDING (never auto-confirmed) + a 'confirm eligibility' to-do."""
    ext = ExtractedActivity(
        provider="Little Monsters",
        activity_name="Little Monsters Summer Camp",
        kid_fit="Alkina",
        age_min=5.0,
        age_max=10.0,
        dates=["2026-07-06", "2026-07-13"],
        hours="9am-3pm",
        location="Healdsburg",
        amount_due=325.0,
        payment_due_date="2026-06-30",
        forms_required=["Liability waiver"],
        action_items=["Register Alkina online"],
        contact=Contact(name="Carey", phone="555-1212"),
        links=[Link(label="Register", url="http://reg")],
    )
    aid = store.insert_ingest_artifact("u1", source="photo", media_type="image")
    created = materialize(
        store, "u1", aid, ext, kids=[{"name": "Alkina", "age": 4}, {"name": "Ceiba", "age": 8}]
    )

    act = store.get_tracked_activity(created["activity_id"])
    assert act["status"] == "pending_eligibility"
    assert "Alkina is 4" in act["pending_reason"]
    assert act["price_amount"] == 325.0
    assert act["price_status"] == "confirmed"

    titles = [t["title"] for t in store.list_todos("u1")]
    assert any("Confirm eligibility" in t for t in titles)
    assert any("Register Alkina" in t for t in titles)
    assert any("Pay $325" in t for t in titles)
    assert any("Liability waiver" in t for t in titles)

    assert len(created["calendar_ids"]) == 2
    # Artifact write-back reflects the extraction.
    assert store.get_ingest_artifact(aid, "u1")["extract_status"] == "extracted"


def test_materialize_eligible_kid_not_pending(store):
    ext = ExtractedActivity(
        provider="Soccer Stars",
        activity_name="Soccer Camp",
        kid_fit="Ceiba",
        age_min=5.0,
        action_items=[],
    )
    aid = store.insert_ingest_artifact("u1", source="paste")
    created = materialize(store, "u1", aid, ext, kids=[{"name": "Ceiba", "age": 8}])
    act = store.get_tracked_activity(created["activity_id"])
    assert act["status"] == "interested"
    assert act["pending_reason"] is None


def test_materialize_no_activity_when_nothing_identified(store):
    """A message with no provider/activity should still record the artifact but
    spawn nothing — no junk tracked rows."""
    ext = ExtractedActivity(action_items=["Call Heather back"])
    aid = store.insert_ingest_artifact("u1", source="imessage")
    created = materialize(store, "u1", aid, ext, kids=[])
    assert created["activity_id"] is None
    assert created["todo_ids"] == []
    assert store.list_tracked_activities("u1") == []
    assert store.get_ingest_artifact(aid, "u1")["extract_status"] == "extracted"


# --------------------------------------------------------------------------- #
# Layer 2: HTTP API (faked LLM)
# --------------------------------------------------------------------------- #

os.environ["MVP_DUCKDB_PATH"] = str(Path(tempfile.mkdtemp()) / "ingest_api.duckdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.ingest.router as ingest_router  # noqa: E402
import app.ingest.extract as ingest_extract  # noqa: E402
import app.cos.router as cos_router  # noqa: E402
import app.server as server  # noqa: E402


def _reconnect_shared_storage():
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _issue_token(client, user_id: str) -> str:
    resp = client.post("/auth/issue-token", json={"user_id": user_id})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


_FAKE_EXTRACT = ExtractedActivity(
    provider="Camp HBG",
    activity_name="Camp HBG Summer",
    kid_fit="Ceiba",
    age_min=5.0,
    dates=["2026-07-06"],
    amount_due=250.0,
    action_items=["Register online"],
    contact=Contact(name="Front Desk", email="info@camphbg.test"),
    links=[Link(label="Register", url="http://camphbg.test/reg")],
)


def test_ingest_http_text_image_and_draft(monkeypatch):
    monkeypatch.setattr(
        ingest_extract, "extract_from_text", lambda *a, **k: _FAKE_EXTRACT
    )
    monkeypatch.setattr(
        ingest_extract, "extract_from_image", lambda *a, **k: _FAKE_EXTRACT
    )

    # Fake the draft-email LLM so it never hits the network.
    class _FakeMsg:
        content = "Hi, I'd like to confirm Ceiba's spot at Camp HBG. Best, [Your name]"

    class _FakeLLM:
        def __init__(self, *a, **k):
            pass

        def invoke(self, *a, **k):
            return _FakeMsg()

    import langchain_openai

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", _FakeLLM)

    try:
        with TestClient(server.app) as client:
            user_id = "ingest-http-test"
            token = _issue_token(client, user_id)
            auth = {"Authorization": f"Bearer {token}"}

            # ── auth gating ───────────────────────────────────────────
            assert (
                client.post(
                    "/ingest/text", json={"user_id": user_id, "text": "x"}
                ).status_code
                == 401
            )
            assert (
                client.post(
                    "/ingest/text",
                    json={"user_id": "someone-else", "text": "x"},
                    headers=auth,
                ).status_code
                == 403
            )

            # ── text ingest happy path ────────────────────────────────
            r = client.post(
                "/ingest/text",
                json={"user_id": user_id, "text": "Camp HBG welcome! Register online.",
                      "source": "paste"},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["extract_status"] == "extracted"
            assert body["extracted"]["provider"] == "Camp HBG"
            assert body["created"]["activity_id"]
            artifact_id = body["artifact_id"]

            # empty text rejected
            assert (
                client.post(
                    "/ingest/text", json={"user_id": user_id, "text": "   "}, headers=auth
                ).status_code
                == 400
            )

            # ── image ingest happy path (multipart) ───────────────────
            png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            r = client.post(
                "/ingest/image",
                data={"user_id": user_id, "source": "photo", "caption": "flyer"},
                files={"file": ("flyer.png", png, "image/png")},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            assert r.json()["extracted"]["provider"] == "Camp HBG"

            # unsupported mime rejected
            r = client.post(
                "/ingest/image",
                data={"user_id": user_id},
                files={"file": ("x.txt", b"hi", "text/plain")},
                headers=auth,
            )
            assert r.status_code == 415

            # ── list + get artifacts ──────────────────────────────────
            r = client.get("/ingest/artifacts", headers=auth)
            assert r.status_code == 200
            assert len(r.json()["artifacts"]) >= 2
            r = client.get(f"/ingest/artifacts/{artifact_id}", headers=auth)
            assert r.status_code == 200
            assert r.json()["id"] == artifact_id
            assert client.get("/ingest/artifacts/does-not-exist", headers=auth).status_code == 404

            # ── draft email (never sends) ─────────────────────────────
            activity_id = body["created"]["activity_id"]
            r = client.post(
                "/cos/draft-email",
                json={"user_id": user_id, "intent": "confirm Ceiba's spot",
                      "activity_id": activity_id},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            d = r.json()
            assert d["sent"] is False
            assert "Camp HBG" in d["draft"]
            assert d["to"] == "info@camphbg.test"  # pulled from contact
    finally:
        _reconnect_shared_storage()
