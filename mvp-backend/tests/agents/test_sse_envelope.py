"""
Envelope contract for the parent /chat SSE stream (app/server.generate_stream).

The iOS app and web dashboard both parse `data: {"type":"token","content":...}`
frames terminated by `data: [DONE]`. If the dependency bump changes how
`astream_events(version="v1")` shapes events (the `event["event"]` kind or
`event["data"]["chunk"].content` access), the envelope would silently break.
We drive the real generator with a fake agent that emits langchain-shaped
events — no network, no real LLM.

Importing app.server triggers the DuckDB bootstrap; that's intentional (it also
proves the server module still imports under the new stack). persist_state is
stubbed so the test never writes to disk.
"""
from __future__ import annotations

import asyncio
import json

import pytest


async def _collect(agen):
    return [chunk async for chunk in agen]


class _FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


async def _fake_astream_events(*args, **kwargs):
    # Mimics the subset of langchain's v1 event stream that generate_stream reads.
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk("Hello")}}
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk(", world")}}
    yield {"event": "on_chat_model_stream", "data": {"chunk": _FakeChunk("")}}  # empty -> skipped
    yield {"event": "on_tool_start", "name": "search", "data": {}}
    yield {"event": "on_tool_end", "name": "search", "data": {}}


class _FakeAgent:
    def astream_events(self, *args, **kwargs):
        return _fake_astream_events(*args, **kwargs)


def _parse_sse(lines):
    """Split a list of raw SSE strings into decoded payloads (or the [DONE] sentinel)."""
    events = []
    for raw in lines:
        assert raw.endswith("\n\n"), f"SSE frame must end with a blank line: {raw!r}"
        body = raw[len("data: "):].strip()
        events.append(body if body == "[DONE]" else json.loads(body))
    return events


def test_generate_stream_envelope(monkeypatch, tmp_path):
    # Redirect storage to a throwaway DB BEFORE importing app.server (it builds
    # DuckDBStorage at module load); otherwise it collides with the dev server's
    # lock on the real data/mvp.duckdb.
    monkeypatch.setenv("MVP_DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    server = pytest.importorskip("app.server")

    monkeypatch.setattr(server, "get_agent", lambda user_id: _FakeAgent())
    monkeypatch.setattr(server, "persist_state", lambda user_id: None)
    monkeypatch.setattr(
        server.chat_memory, "get_thread_messages", lambda user_id, thread_id: []
    )

    raw = asyncio.run(_collect(server.generate_stream("hi", "t1", "u1")))
    events = _parse_sse(raw)

    # Token frames carry type/content; empty content is filtered out.
    tokens = [e for e in events if isinstance(e, dict) and e.get("type") == "token"]
    assert [t["content"] for t in tokens] == ["Hello", ", world"]

    # Tool lifecycle frames preserved.
    assert {"type": "tool_start", "tool": "search"} in events
    assert {"type": "tool_end", "tool": "search"} in events

    # Stream terminates with the [DONE] sentinel as the final frame.
    assert events[-1] == "[DONE]"
