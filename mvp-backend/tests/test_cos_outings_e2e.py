"""End-to-end HTTP test of the quick-outings path through the real /cos/chat
route (app/cos/router.py), driven with FastAPI's TestClient.

The COS *agent* is faked — but unlike test_cos_api's pure-text fake, this fake
actually INVOKES the real SuggestOutings tool (with only the two external calls,
Tavily + the synthesis LLM, stubbed). So the whole chain runs for real: the route,
auth, SSE envelope, the tool wrapper, and the standalone outings module — the only
things faked are the network/LLM, exactly as the rest of the suite is hermetic.

What it proves:
- the route surfaces `tool_start`/`tool_end` frames for SuggestOutings;
- the streamed reply is grounded (the resolved weekend + an idea);
- the flow is EPHEMERAL — the board and the tracked-activities list are byte-for-byte
  unchanged before vs. after the outing turn (no card, no to-do).

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["MVP_DUCKDB_PATH"] = str(Path(tempfile.mkdtemp()) / "cos_outings_e2e.duckdb")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.cos.router as cos_router  # noqa: E402
import app.cos.outings as outings  # noqa: E402
import app.cos.tools as cos_tools  # noqa: E402
import app.server as server  # noqa: E402
from app.profiling import profiling_service  # noqa: E402

USER = "outings-e2e-user"


class _FixedDate(_dt.date):
    """Pin date.today() so 'this weekend' resolves deterministically (2026-07-10 is
    a Friday → Sat Jul 11 / Sun Jul 12), regardless of when the suite runs."""

    @classmethod
    def today(cls):
        return cls(2026, 7, 10)


# --------------------------------------------------------------------------- #
# External fakes (Tavily + synthesis) — the ONLY things stubbed
# --------------------------------------------------------------------------- #
class _FakeTavily:
    def __init__(self, *a, **k):
        pass

    def invoke(self, *a, **k):
        return {"results": [
            {"title": "California Academy of Sciences", "url": "https://calacademy.org",
             "content": "Aquarium, stroller-friendly, Golden Gate Park."},
        ]}


class _FakeStructured:
    def invoke(self, *a, **k):
        return outings._OutingList(outings=[
            outings.Outing(
                title="California Academy of Sciences", where="Golden Gate Park",
                why_it_fits="calm indoor exhibits for a toddler + baby",
                good_to_know="stroller-friendly; changing tables; nap-friendly midday",
                url="https://calacademy.org",
            ),
        ])


class _FakeChat:
    def __init__(self, *a, **k):
        pass

    def with_structured_output(self, *a, **k):
        return _FakeStructured()


# --------------------------------------------------------------------------- #
# Fake agent that drives the REAL SuggestOutings tool
# --------------------------------------------------------------------------- #
class _FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


class _OutingsAgent:
    """astream_events invokes the real SuggestOutings tool and streams its reply,
    bracketed by tool_start/tool_end frames named 'SuggestOutings'."""

    def __init__(self, user_id: str) -> None:
        self._tool = next(
            t for t in cos_tools.build_cos_tools(user_id) if t.name == "SuggestOutings"
        )

    async def _events(self, *args, **kwargs):
        yield {"event": "on_tool_start", "name": "SuggestOutings", "data": {}}
        reply = self._tool.invoke(
            {"location": "San Francisco", "when": "this weekend", "count": 3}
        )
        yield {"event": "on_tool_end", "name": "SuggestOutings", "data": {}}
        # Stream the grounded reply as the assistant message.
        for piece in (reply[: len(reply) // 2], reply[len(reply) // 2:]):
            yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk(piece)}}

    def astream_events(self, *args, **kwargs):
        return self._events(*args, **kwargs)


def _issue_token(client, user_id: str) -> str:
    resp = client.post("/auth/issue-token", json={"user_id": user_id})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def _parse_sse(text: str):
    import json

    events = []
    for raw in text.split("\n\n"):
        raw = raw.strip()
        if not raw:
            continue
        body = raw[len("data: "):]
        events.append(body if body == "[DONE]" else json.loads(body))
    return events


def _reconnect_shared_storage():
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _seed_sf_family():
    profiling_service._profiles.pop(USER, None)  # type: ignore[attr-defined]
    profiling_service.update_parent_profile(
        USER, {"name": "Sam", "postal_code": "94110", "country": "US"}
    )
    profiling_service.update_child_profile(USER, "Nova", {"name": "Nova", "age": "2.5"})
    profiling_service.update_child_profile(USER, "Baby", {"name": "Baby", "age": "0.4"})


def test_quick_outings_streams_and_stays_ephemeral(monkeypatch):
    monkeypatch.setattr("langchain_tavily.TavilySearch", _FakeTavily)
    monkeypatch.setattr(outings, "ChatOpenAI", _FakeChat)
    monkeypatch.setattr(outings, "date", _FixedDate)  # deterministic "this weekend"
    monkeypatch.setattr(
        cos_router, "get_cos_agent", lambda user_id: _OutingsAgent(user_id)
    )
    _seed_sf_family()

    try:
        _run()
    finally:
        _reconnect_shared_storage()


def _run():
    with TestClient(server.app) as client:
        token = _issue_token(client, USER)
        auth = {"Authorization": f"Bearer {token}"}

        # ── Snapshot the plan BEFORE the outing turn ──────────────────
        board_before = client.get("/cos/plan/board", headers=auth).json()
        acts_before = client.get("/cos/activities", headers=auth).json()["activities"]
        assert acts_before == []  # clean slate

        # ── The outing ask ────────────────────────────────────────────
        with client.stream(
            "POST",
            "/cos/chat",
            json={
                "user_id": USER,
                "message": "what can we do with the kids in the city this weekend?",
            },
            headers=auth,
        ) as resp:
            assert resp.status_code == 200
            body = "".join(resp.iter_text())
        events = _parse_sse(body)

        # (a) the route surfaced the SuggestOutings tool frames
        tool_names = {
            e.get("tool") for e in events
            if isinstance(e, dict) and e.get("type") in ("tool_start", "tool_end")
        }
        assert "SuggestOutings" in tool_names

        # (b) the streamed reply is grounded (resolved weekend + an idea) …
        reply = "".join(
            e["content"] for e in events
            if isinstance(e, dict) and e.get("type") == "token"
        )
        assert "California Academy of Sciences" in reply
        assert "Jul 11" in reply and "Jul 12" in reply  # this weekend resolved
        assert "not saved to the plan" in reply  # ephemerality signalled
        assert events[-1] == "[DONE]"

        # (c) EPHEMERAL — nothing landed on the board or the activity list
        board_after = client.get("/cos/plan/board", headers=auth).json()
        acts_after = client.get("/cos/activities", headers=auth).json()["activities"]
        assert acts_after == []
        assert acts_after == acts_before
        assert board_after == board_before
