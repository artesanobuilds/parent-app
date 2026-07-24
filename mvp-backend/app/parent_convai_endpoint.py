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
import time
import uuid
from typing import List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agent import get_agent
# Reuse the kid endpoint's OpenAI-SSE helpers + the shared secret.
from app.convai_endpoint import (
    CONVAI_SECRET,
    _ms,
    _openai_delta,
    _openai_done,
    _probe_stream,
    _trailing_silence_nudges,
    _voice_perf_metrics,
)
from app.thread_repair import is_dangling_tool_error, repair_thread

logger = logging.getLogger(__name__)

router = APIRouter()

# Matches the content links the parent agent emits. `id` stops at the closing
# paren; whitespace guards against accidental over-capture.
_LINK_RE = re.compile(r"\[([^\]]*)\]\(mvp://(library|community)/([^)\s]+)\)")
_HOLD_CAP = 120  # backstop: never buffer a "pending link" longer than this
_LINK_TARGETS = ("mvp://library/", "mvp://community/")
_MAX_LABEL = 80  # a content title; anything longer isn't a link label


def _is_plausible_link(tail: str) -> bool:
    """Could `tail` (which starts at a '[') still become an mvp:// link once more
    tokens arrive?

    This is the whole point of the hold. The old rule — hold everything after the
    last '[' until a link closes or 300 chars pile up — stalled speech for up to
    300 characters on ANY bracketed aside in prose, which the parent hears as the
    coach going silent mid-sentence. Now we hold only while the tail is still on a
    path to a real link, and flush the instant it can't be one:

      "[Some tit"              → inside the label      → plausible
      "[Some title]"           → label just closed     → plausible
      "[Some title](mvp://li"  → target prefix-matches → plausible
      "[sic] and then"         → prose aside           → flush now
      "[docs](https://…"       → not an mvp:// target  → flush now
    """
    close = tail.find("]")
    if close == -1:
        # Still inside the label. A "label" this long is prose, not a title.
        return len(tail) - 1 <= _MAX_LABEL
    if close - 1 > _MAX_LABEL:
        return False
    rest = tail[close + 1:]
    if not rest:
        return True                       # "[label]" — the "](" may be next chunk
    if not rest.startswith("("):
        return False                      # "[label] more prose" — never a link
    partial = rest[1:]
    # Prefix-compatible in either direction: "mvp://li" is a partial of the target,
    # "mvp://library/abc" is the target plus an id we're still waiting to close.
    return any(t.startswith(partial) or partial.startswith(t) for t in _LINK_TARGETS)


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
        # Hold from the last '[' ONLY while that tail is still a plausible link in
        # progress — a real link must never leak its URL into speech, but ordinary
        # bracketed prose must not stall it either. _HOLD_CAP stays as a backstop
        # for the pathological case (e.g. "[t](mvp://library/" that never closes).
        idx = self._buf.rfind("[")
        tail = self._buf[idx:] if idx != -1 else ""
        if idx == -1 or len(tail) > _HOLD_CAP or not _is_plausible_link(tail):
            safe, self._buf = self._buf, ""
        else:
            safe, self._buf = self._buf[:idx], tail
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
    saw_user_msg = False
    for m in reversed(messages):
        if m.get("role") == "user":
            saw_user_msg = True
            last_user_msg = m.get("content", "")
            break

    # A turn-timeout nudge ("..."/empty) is a valid turn, not a malformed
    # request — route it to the canned check-in instead of 400ing.
    silence_nudges = _trailing_silence_nudges(messages) if saw_user_msg else 0
    if not last_user_msg and not silence_nudges:
        raise HTTPException(status_code=400, detail="no user message found")

    return StreamingResponse(
        _stream_response(user_id, thread_id, last_user_msg,
                         silence_nudges=silence_nudges),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_response(user_id: str, thread_id: str, message: str,
                           silence_nudges: int = 0):
    turn_started = time.monotonic()
    chat_id = uuid.uuid4().hex[:12]

    # Turn-timeout nudge: the parent has gone quiet, not asked something. Speak
    # a short check-in instead of running the agent — deterministic and instant,
    # never re-answers the previous turn, and keeps phantom "..." turns out of
    # the LangGraph thread (no repair/agent/LLM involved at all).
    if silence_nudges:
        import random
        from app.cost_logging import log_perf, new_workflow_id
        if silence_nudges == 1:
            line = random.choice([
                "Still there? No rush.",
                "Take your time — I'm right here.",
                "Still with me?",
            ])
        elif silence_nudges == 2:
            line = "No hurry at all. I'll be here when you're ready."
        else:
            line = "I'll stay on the line — if you're done for now, just say goodbye or tap End."
        yield _openai_delta(content=line, chat_id=chat_id)
        yield _openai_done()
        ms = _ms(turn_started)
        log_perf("VOICE", feature="parent_voice", workflow=new_workflow_id(),
                 session=thread_id, user=user_id, ttfb_ms=ms, total_ms=ms,
                 chunks=1, tool_turn=0)
        _voice_perf_metrics("parent_voice", repair_ms=None, model_ttft_ms=None,
                            ttfb_ms=ms, tool_turn=0, outcome="silence")
        return

    agent = get_agent(user_id)
    from app.cost_logging import CostLoggingCallbackHandler, log_perf, new_workflow_id
    # ONE id for the whole voice turn, shared by the cost handler and the perf
    # line so a turn's spend and its latency join on `workflow=`.
    voice_wf = new_workflow_id()
    _voice_cost = CostLoggingCallbackHandler(
        feature="parent_voice", workflow=voice_wf, session=thread_id, user=user_id
    )
    # NOTE: voice memory is its own thread (thread_id "default") — the text
    # /chat path uses a per-install UUID thread, so the two do NOT share
    # history today. Unifying them is a product decision, tracked in the plan.
    config = {"configurable": {"thread_id": f"{user_id}:{thread_id}"}, "callbacks": [_voice_cost]}

    # Self-heal before the turn: a prior cancelled turn (ElevenLabs barge-in /
    # timeout abort) can leave a dangling tool call that would 400 every
    # request on this thread forever. See app/thread_repair.py.
    repair_started = time.monotonic()
    await repair_thread(agent, config)
    repair_ms = _ms(repair_started)

    # Turn timings. `model_ttft_ms` is when the model's first token reached US;
    # `ttfb_ms` is when the first delta reached ElevenLabs. The gap between them
    # is OUR buffering (the link stripper's partial-link hold) — the shrinkable part.
    # Deliberately NOT reset per retry attempt: the parent's wait started at t0.
    model_ttft_ms: Optional[int] = None
    ttfb_ms: Optional[int] = None
    chunks = 0
    tool_turn = 0
    perf_emitted = False

    def _mark_yield(content: bool = True) -> None:
        """Call immediately before yielding to ElevenLabs. Tool-call deltas still
        move TTFB (they're bytes on the wire) but aren't spoken, so they don't
        count as chunks."""
        nonlocal ttfb_ms, chunks
        if ttfb_ms is None:
            ttfb_ms = _ms(turn_started)
        if content:
            chunks += 1

    def _emit_perf(outcome: str) -> None:
        """Exactly one [PERF][VOICE] line per turn, error path included — a turn
        that failed is precisely the one worth timing."""
        nonlocal perf_emitted
        if perf_emitted:
            return
        perf_emitted = True
        log_perf(
            "VOICE", feature="parent_voice", workflow=voice_wf, session=thread_id,
            user=user_id, repair_ms=repair_ms, model_ttft_ms=model_ttft_ms,
            ttfb_ms=ttfb_ms, total_ms=_ms(turn_started), chunks=chunks,
            tool_turn=tool_turn,
        )
        _voice_perf_metrics(
            "parent_voice", repair_ms=repair_ms, model_ttft_ms=model_ttft_ms,
            ttfb_ms=ttfb_ms, tool_turn=tool_turn, outcome=outcome,
        )

    try:
        for attempt in (1, 2):
            stripper = _LinkStripper()
            yielded = False
            try:
                # version="v2" is the cheaper event API — v1 builds a much heavier
                # event payload per token, pure overhead on a voice hot path where
                # every ms is audible. Our two filters are identical across versions.
                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=message)]},
                    config=config,
                    version="v2",
                ):
                    if event["event"] != "on_chat_model_stream":
                        # A tool ran before the first spoken token — that turn's
                        # latency belongs in its own bucket, not the plain-answer one.
                        if event["event"] == "on_tool_start" and model_ttft_ms is None:
                            tool_turn = 1
                        continue
                    content = event["data"]["chunk"].content
                    # In v2 a chunk's content can be a LIST of content blocks (tool-call
                    # deltas), not a str. Feeding that to the link stripper would blow up
                    # mid-turn, so skip anything that isn't spoken text.
                    if not content or not isinstance(content, str):
                        continue
                    if model_ttft_ms is None:
                        model_ttft_ms = _ms(turn_started)  # before the link-stripper hold
                    safe, tools = stripper.feed(content)
                    if safe:
                        yielded = True
                        _mark_yield()
                        yield _openai_delta(content=safe, chat_id=chat_id)
                    for kind, cid in tools:
                        yielded = True
                        _mark_yield(content=False)
                        yield _show_content_tool_delta(kind, cid, chat_id)

                tail = stripper.flush()
                if tail:
                    _mark_yield()
                    yield _openai_delta(content=tail, chat_id=chat_id)
                yield _openai_done()
                _emit_perf("ok")
                return

            except Exception as exc:
                # Poisoned mid-run (e.g. a concurrent voice request cancelled a
                # tool call after our pre-flight check): repair and retry once,
                # but only if nothing streamed yet — a retry after spoken output
                # would repeat the sentence to the parent.
                if attempt == 1 and not yielded and is_dangling_tool_error(exc):
                    logger.warning(
                        "[parent-convai] dangling tool call mid-run — repairing and "
                        "retrying user=%s thread=%s", user_id, thread_id,
                    )
                    await repair_thread(agent, config)
                    continue
                logger.exception(
                    "[parent-convai] stream error user=%s thread=%s", user_id, thread_id
                )
                _mark_yield()
                yield _openai_delta(
                    content="I hit a snag on my end — give me a second, then ask me again.",
                    chat_id=chat_id,
                )
                yield _openai_done()
                _emit_perf("error")
                return
    finally:
        # A barge-in is the MOST common way a voice turn ends, and it unwinds
        # this generator without reaching either exit above. Emitting only on
        # the clean exits would silently drop every interrupted turn out of the
        # latency histogram — leaving it measuring the turns nobody minded
        # waiting for. No-ops (perf_emitted) when the turn already reported.
        _emit_perf("interrupted")
