"""
OpenAI-compatible Custom-LLM endpoint for the PARENT coaching agent over
ElevenLabs Conversational AI.

Unlike the kid endpoint (app/convai_endpoint.py) this has NO moderation, crisis
lock, PIN, or end_call — the parent is a consenting adult. Its novel job is
turning the agent's inline content links into a clean voice experience:

  The parent agent weaves `[Title](mvp://library/{id})` / `mvp://community/{id})`
  markdown links into its prose. TTS must NOT read a URL aloud, and the app
  needs a structured trigger to render the card. So as we stream, we:
    - emit the human label as spoken text and DROP the `(mvp://…)`
    - emit an OpenAI tool-call delta (`show_article` / `show_community_post`,
      arguments `{"id": ...}`) that ElevenLabs forwards to the iOS client tool.

Auth: same shared secret as the kid endpoint (Authorization: Bearer or
X-ElevenLabs-Secret).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agent import get_agent
# Reuse the kid endpoint's OpenAI-SSE helpers + the shared secret.
from app.convai_endpoint import (
    CONVAI_SECRET,
    _openai_delta,
    _openai_done,
    _probe_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Matches the content links the parent agent emits. `id` stops at the closing
# paren; whitespace guards against accidental over-capture.
_LINK_RE = re.compile(r"\[([^\]]*)\]\(mvp://(library|community)/([^)\s]+)\)")
_HOLD_CAP = 300  # don't buffer a "pending link" longer than this before flushing


class _LinkStripper:
    """Incrementally strip mvp:// content links from streamed text, emitting the
    human label as speech and surfacing (kind, id) pairs to fire client tools.
    Holds a trailing partial so a link split across token chunks still matches."""

    def __init__(self) -> None:
        self._buf = ""

    def feed(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._buf += text
        out: List[str] = []
        tools: List[Tuple[str, str]] = []
        while True:
            m = _LINK_RE.search(self._buf)
            if not m:
                break
            out.append(self._buf[: m.start()])   # text before the link
            out.append(m.group(1))               # speak the label, drop the URL
            tools.append((m.group(2), m.group(3)))
            self._buf = self._buf[m.end():]
        # Hold from the last '[' (a possible partial link) so we don't emit half
        # a link; cap the hold so non-link brackets don't stall the stream.
        idx = self._buf.rfind("[")
        if idx == -1 or (len(self._buf) - idx) > _HOLD_CAP:
            safe, self._buf = self._buf, ""
        else:
            safe, self._buf = self._buf[:idx], self._buf[idx:]
        return "".join(out) + safe, tools

    def flush(self) -> str:
        s, self._buf = self._buf, ""
        return s


def _show_content_tool_delta(kind: str, content_id: str, chat_id: str) -> str:
    """OpenAI tool-call delta for a display-only client tool. finish_reason stays
    null (non-terminal) so the agent keeps talking — contrast the kid endpoint's
    end_call which terminates the turn."""
    name = "show_article" if kind == "library" else "show_community_post"
    delta = {
        "tool_calls": [{
            "index": 0,
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps({"id": content_id})},
        }]
    }
    obj = {
        "id": f"chatcmpl-{chat_id}",
        "object": "chat.completion.chunk",
        "choices": [{"delta": delta, "index": 0, "finish_reason": None}],
    }
    return f"data: {json.dumps(obj)}\n\n"


@router.post("/v1/parent/chat/completions")
async def parent_convai_chat_completions(
    request: Request,
    x_elevenlabs_secret: Optional[str] = Header(default=None, alias="X-ElevenLabs-Secret"),
    authorization: Optional[str] = Header(default=None),
):
    bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
    presented = x_elevenlabs_secret or bearer
    if not CONVAI_SECRET or presented != CONVAI_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret")

    body = await request.json()
    messages = body.get("messages", [])
    raw_extra = body.get("elevenlabs_extra_body")
    extra = raw_extra or {}

    user_id = extra.get("user_id")
    thread_id = extra.get("thread_id", "default")

    # Bare connection-test probe (no extra_body) → valid stub stream.
    if not user_id:
        if not raw_extra:
            return StreamingResponse(
                _probe_stream(), media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        raise HTTPException(status_code=400, detail="missing user_id in elevenlabs_extra_body")

    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    if not last_user_msg:
        raise HTTPException(status_code=400, detail="no user message found")

    return StreamingResponse(
        _stream_response(user_id, thread_id, last_user_msg),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_response(user_id: str, thread_id: str, message: str):
    chat_id = uuid.uuid4().hex[:12]
    agent = get_agent(user_id)
    # Share the thread with the text /chat path so the agent remembers across
    # voice and text (same memory_key convention as server.generate_stream).
    config = {"configurable": {"thread_id": f"{user_id}:{thread_id}"}}
    stripper = _LinkStripper()

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1",
        ):
            if event["event"] != "on_chat_model_stream":
                continue
            content = event["data"]["chunk"].content
            if not content:
                continue
            safe, tools = stripper.feed(content)
            if safe:
                yield _openai_delta(content=safe, chat_id=chat_id)
            for kind, cid in tools:
                yield _show_content_tool_delta(kind, cid, chat_id)

        tail = stripper.flush()
        if tail:
            yield _openai_delta(content=tail, chat_id=chat_id)
        yield _openai_done()

    except Exception:
        logger.exception("[parent-convai] stream error")
        yield _openai_delta(content="Sorry — something went wrong. Let's try again.", chat_id=chat_id)
        yield _openai_done()
