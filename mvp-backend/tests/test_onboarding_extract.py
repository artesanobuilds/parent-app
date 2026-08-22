"""Pre-account onboarding extraction (Heisman sprint-01, step 04).

Locks the anon-session + extract contract in app/onboarding_extract.py:

  • /onboarding/anon-session mints a scoped token and /onboarding/extract
    accepts it end-to-end, returning the model's structured activities (the
    LLM is mocked — the endpoint imports `from app.agent import llm` INSIDE
    the handler, so patching app.agent.llm is sufficient).
  • The SECURITY PROPERTY that matters most: the anon token and a real user
    access token are NOT interchangeable in either direction. A real access
    token (has `sub`, no `scope`) must be rejected by /onboarding/extract,
    and the anon token (has `scope`, NO `sub`) must be rejected by every
    authenticated endpoint (GET /profile here). One signing secret, two
    disjoint doors.
  • Input caps: 422 on an empty body and on a disallowed media_type; 413 on
    oversize text.
  • Kill switch: ONBOARDING_EXTRACT_ENABLED=0 → 503 on both routes.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing
app.server, mirroring tests/test_delete_memory_eviction.py, and the storage
singleton is rebuilt in teardown (TestClient exit closes storage — every
TestClient module must reconnect, see memory
debugging_testclient_storage_singleton).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "onboarding_extract.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
# The "extract" class is read at import time by app.rate_limit; the shared
# per-IP bucket ("testclient") would otherwise cap the whole suite at 30/hr.
os.environ.setdefault("RATE_LIMIT_EXTRACT_PER_HOUR", "100000")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


# --------------------------------------------------------------------------- #
# LLM fake
# --------------------------------------------------------------------------- #


class _FakeLLM:
    """Stands in for app.agent.llm: with_structured_output(...).invoke(...)."""

    def __init__(self, result):
        self._result = result
        self.calls = []

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, messages, config=None):
        self.calls.append({"messages": messages, "config": config})
        return self._result


def _fake_extraction():
    from app.onboarding_extract import ExtractedActivity, _Extraction

    return _Extraction(activities=[
        ExtractedActivity(
            who="Lily",
            what="Swim lessons",
            when="Tuesdays · 4:15 pm",
            where="Northgate Aquatic Center",
            notes="Bring goggles",
        ),
        ExtractedActivity(who="you", what="Bake-sale signup", when="", where="", notes=""),
    ])


# --------------------------------------------------------------------------- #
# (a) happy path: anon-session → extract, end to end
# --------------------------------------------------------------------------- #


def test_anon_session_then_extract_end_to_end(monkeypatch):
    from fastapi.testclient import TestClient
    import app.agent as agent_mod
    import app.server as server

    fake = _FakeLLM(_fake_extraction())
    monkeypatch.setattr(agent_mod, "llm", fake)

    try:
        with TestClient(server.app) as client:
            r = client.post("/onboarding/anon-session")
            assert r.status_code == 200, r.text
            session = r.json()
            assert session["token"] and session["expires_in"] > 0

            r = client.post(
                "/onboarding/extract",
                json={"text": "Lily has swim lessons Tuesdays 4:15 at Northgate Aquatic Center"},
                headers={"Authorization": f"Bearer {session['token']}"},
            )
            assert r.status_code == 200, r.text
            acts = r.json()["activities"]
            assert [a["what"] for a in acts] == ["Swim lessons", "Bake-sale signup"]
            assert acts[0] == {
                "who": "Lily",
                "what": "Swim lessons",
                "when": "Tuesdays · 4:15 pm",
                "where": "Northgate Aquatic Center",
                "notes": "Bring goggles",
            }
            # The handler really consulted the (mocked) model, with the parent's
            # scrap in the user turn.
            assert len(fake.calls) == 1
            from app.onboarding_extract import _Extraction
            assert fake.schema is _Extraction
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# (b) no/garbage token → 401
# --------------------------------------------------------------------------- #


def test_extract_rejects_missing_and_garbage_tokens():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            body = {"text": "swim lessons tuesday"}
            assert client.post("/onboarding/extract", json=body).status_code == 401
            assert client.post(
                "/onboarding/extract", json=body,
                headers={"Authorization": "Bearer not-a-jwt"},
            ).status_code == 401
            assert client.post(
                "/onboarding/extract", json=body,
                headers={"Authorization": "Bearer aa.bb.cc"},
            ).status_code == 401
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# (c) THE security property: the two token kinds never cross doors
# --------------------------------------------------------------------------- #


def test_user_token_and_anon_token_are_not_interchangeable():
    """A real access token must not open /onboarding/extract (scope check),
    and the anon token must not open any user endpoint (no `sub` → it is not
    a user credential). If either direction ever passes, the anon mint
    endpoint becomes a free authentication bypass or vice versa."""
    from fastapi.testclient import TestClient
    from app.auth import mint_access_token
    from app.onboarding_extract import mint_anon_session_token
    import app.server as server

    try:
        with TestClient(server.app) as client:
            user_token, _ = mint_access_token("extract-scope-user")
            r = client.post(
                "/onboarding/extract",
                json={"text": "swim lessons tuesday"},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert r.status_code == 401, (
                "a REAL user access token opened /onboarding/extract — the "
                "scope=onboarding_extract check is gone"
            )

            anon_token, _ = mint_anon_session_token()
            r = client.get("/profile", headers={"Authorization": f"Bearer {anon_token}"})
            assert r.status_code == 401, (
                "the anon extraction token authenticated GET /profile — a "
                "sub-less scoped token must never resolve to a user"
            )
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# (d) input caps: 422 empty / bad media_type, 413 oversize
# --------------------------------------------------------------------------- #


def test_extract_input_caps(monkeypatch):
    import base64

    from fastapi.testclient import TestClient
    import app.agent as agent_mod
    import app.server as server

    # A fake model that would blow up if any capped input ever reached it.
    class _MustNotBeCalled:
        def with_structured_output(self, schema):
            raise AssertionError("capped input reached the model")

    monkeypatch.setattr(agent_mod, "llm", _MustNotBeCalled())

    try:
        with TestClient(server.app) as client:
            token = client.post("/onboarding/anon-session").json()["token"]
            auth = {"Authorization": f"Bearer {token}"}

            # empty body — neither text nor image
            assert client.post("/onboarding/extract", json={}, headers=auth).status_code == 422
            assert client.post(
                "/onboarding/extract", json={"text": "   "}, headers=auth,
            ).status_code == 422

            # disallowed media type
            png_b64 = base64.b64encode(b"not-really-a-gif").decode()
            r = client.post(
                "/onboarding/extract",
                json={"image_b64": png_b64, "media_type": "image/gif"},
                headers=auth,
            )
            assert r.status_code == 422

            # oversize text
            r = client.post(
                "/onboarding/extract",
                json={"text": "x" * 8_001},
                headers=auth,
            )
            assert r.status_code == 413
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# (e) kill switch
# --------------------------------------------------------------------------- #


def test_kill_switch_disables_both_routes(monkeypatch):
    from fastapi.testclient import TestClient
    from app.onboarding_extract import mint_anon_session_token
    import app.server as server

    monkeypatch.setenv("ONBOARDING_EXTRACT_ENABLED", "0")

    try:
        with TestClient(server.app) as client:
            assert client.post("/onboarding/anon-session").status_code == 503
            token, _ = mint_anon_session_token()
            r = client.post(
                "/onboarding/extract",
                json={"text": "swim lessons tuesday"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 503
    finally:
        _reconnect_shared_storage(server)
