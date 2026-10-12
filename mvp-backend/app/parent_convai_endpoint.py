"""
OpenAI-compatible Custom-LLM endpoint for the PARENT coaching agent over
ElevenLabs Conversational AI.

Unlike the kid endpoint (app/convai_endpoint.py) this has NO moderation, crisis
lock, PIN, or end_call — the parent is a consenting adult. Its novel job is
turning the agent's inline content links into a clean voice experience:

  The parent agent weaves `[Title](mvp://library/{id})` markdown links into its
  prose. TTS must NOT read a URL aloud, and the app needs a structured trigger
  to render the card. So as we stream, we:
    - emit the human label as spoken text and DROP the `(mvp://…)`
    - emit an OpenAI tool-call delta (`show_article`, arguments `{"id": ...}`)
      that ElevenLabs forwards to the iOS client tool.

  `mvp://community/…` is a RETIRED shape (the board is gone; its tables were
  dropped in migration v21). The regex still recognises it so a stale link can
  never leak its URL into speech, but it fires NO client tool — `show_article`
  is the only tool this endpoint emits.

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

from app import agent as agent_module
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

# Compatibility exports preserve callers and tests.
from app.agent_runtime.adapters.voice import (
    _LinkStripper, _is_plausible_link, _show_content_tool_delta,
    _MAX_LABEL, _HOLD_CAP, _LINK_RE, _LINK_TARGETS,
)


def get_agent(user_id: str):
    """Use the trusted voice prompt in the graph that actually answers."""
    return agent_module.get_agent(user_id, surface="voice")


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


def _storage():
    from app.agent_runtime.dependencies import get
    try:
        return get().storage
    except RuntimeError:
        # Compatibility for direct adapter callers outside an ASGI lifespan.
        from app.server import storage_backend
        return storage_backend


async def _stream_response(user_id: str, thread_id: str, message: str,
                           silence_nudges: int = 0):
    from contextlib import aclosing
    from app.agent_runtime.context import RunContext
    from app.agent_runtime.policies import shared_execution_enabled
    from app.agent_runtime.service import owned_stream, RunInterrupted
    from app.agent_runtime.sessions import resolve_parent_thread
    from app.agent_runtime.durability import scope_for

    shared = shared_execution_enabled("parent_voice")
    # Silence prompts are deterministic presentation, not persisted agent turns.
    if silence_nudges:
        async with aclosing(_stream_response_impl(user_id, thread_id, message,
                                                 silence_nudges)) as events:
            async for event in events:
                yield event
        return
    context = RunContext(user_id, "parent_voice", resolve_parent_thread(user_id, "voice", thread_id))

    async def legacy(disconnected):
        terminal = None
        with scope_for(_storage())(context):
            async with aclosing(_stream_response_impl(user_id, thread_id, message,
                                shared=False, context=context, disconnected=disconnected)) as events:
                async for event in events:
                    if event == _openai_done():
                        terminal = event
                    else:
                        yield event
            if disconnected.is_set():
                raise RunInterrupted("Voice turn disconnected before completion")
        if terminal is not None:
            yield terminal

    try:
        stream = (_stream_response_impl(user_id, thread_id, message, shared=True, context=context)
                  if shared else owned_stream(context, legacy))
        async with aclosing(stream) as events:
            async for event in events:
                yield event
    except RunInterrupted:
        logger.info("[parent-convai] voice turn interrupted run=%s", context.run_id)
    except Exception:
        logger.exception("[parent-convai] admission/execution failed")
        yield _openai_delta(
            content="I hit a snag on my end — give me a second, then ask me again.",
            chat_id=uuid.uuid4().hex[:12])
        # No successful terminator when durable finalization or scope exit failed.


async def _stream_response_impl(user_id: str, thread_id: str, message: str,
                                silence_nudges: int = 0, *, shared=False, context=None, disconnected=None):
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

    agent = None if shared else get_agent(user_id)
    from app.cost_logging import CostLoggingCallbackHandler, log_perf, new_workflow_id
    # ONE id for the whole voice turn, shared by the cost handler and the perf
    # line so a turn's spend and its latency join on `workflow=`.
    voice_wf = context.run_id
    _voice_cost = CostLoggingCallbackHandler(
        feature="parent_voice", workflow=voice_wf, session=thread_id, user=user_id
    )
    # NOTE: voice memory is its own thread. The coach and Chief-of-Staff TEXT
    # surfaces were merged onto one per-parent thread (`{user}:parent`), but a
    # spoken turn and a typed turn still pace differently, so voice keeps its
    # own namespace — unifying it too remains a product decision.
    config = {
        "configurable": {"thread_id": agent_module.thread_key(user_id, "voice", thread_id)},
        "callbacks": [_voice_cost],
    }

    # Self-heal before the turn: a prior cancelled turn (ElevenLabs barge-in /
    # timeout abort) can leave a dangling tool call that would 400 every
    # request on this thread forever. See app/thread_repair.py.
    from app.agent_runtime.durability import (
        append_transcript, scope_for, reconcile_receipts, repair_with_receipts, ensure_connected,
    )
    storage = _storage()
    def before(_context):
        append_transcript(storage, context, "parent_voice_threads", thread_id, "user", message)

    def finalize(_context, text):
        if text:
            append_transcript(storage, context, "parent_voice_threads", thread_id, "assistant", text)

    repair_started = time.monotonic()
    if not shared:
        before(context)
        await repair_with_receipts(context, agent, config, repair_thread)
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

    async def graph_events():
        from contextlib import aclosing
        from app.agent_runtime.context import RunContext
        from app.agent_runtime.events import normalize
        from app.agent_runtime.service import execution_service

        async def timed_repair(graph, run_config):
            nonlocal repair_ms
            started = time.monotonic()
            await repair_thread(graph, run_config)
            repair_ms = _ms(started)

        if shared:
            async with aclosing(execution_service.stream(
                    agent, {"messages": [HumanMessage(content=message)]}, config, context,
                    version="v2", repair=timed_repair,
                    is_internal=agent_module.is_internal_event,
                    is_retryable=is_dangling_tool_error,
                    scope=scope_for(storage), reconcile=reconcile_receipts,
                    before=before, finalize=finalize,
                    agent_factory=lambda: get_agent(user_id))) as events:
                async for event in events:
                    yield event
        else:
            ensure_connected(disconnected)
            transcript = []
            async with aclosing(agent.astream_events(
                    {"messages": [HumanMessage(content=message)]}, config=config,
                    version="v2")) as events:
                async for raw in events:
                    if not agent_module.is_internal_event(raw):
                        event = normalize(raw)
                        if event is not None:
                            if event.kind == "token":
                                transcript.append(event.content)
                            yield event
            ensure_connected(disconnected)
            finalize(context, "".join(transcript))

    try:
        for attempt in ((1,) if shared else (1, 2)):
            stripper = _LinkStripper()
            yielded = False
            tool_started = False
            completed = False
            try:
                # version="v2" is the cheaper event API — v1 builds a much heavier
                # event payload per token, pure overhead on a voice hot path where
                # every ms is audible. Our two filters are identical across versions.
                from contextlib import aclosing
                async with aclosing(graph_events()) as events:
                    async for event in events:
                        if event.kind == "completed":
                            completed = True
                        if event.kind == "tool_start":
                            tool_started = True
                        if event.kind != "token":
                            if event.kind == "tool_start" and model_ttft_ms is None:
                                tool_turn = 1
                            continue
                        content = event.content
                        if model_ttft_ms is None:
                            model_ttft_ms = _ms(turn_started)  # before the link-stripper hold
                        safe, tools = stripper.feed(content)
                        if safe:
                            yielded = True
                            _mark_yield()
                            yield _openai_delta(content=safe, chat_id=chat_id)
                        for kind, cid in tools:
                            # A retired mvp://community/ link is stripped from speech
                            # (above) but fires nothing — there is no card to show.
                            if kind != "library":
                                continue
                            yielded = True
                            _mark_yield(content=False)
                            yield _show_content_tool_delta(cid, chat_id)

                # Family cancellation can exhaust the owned iterator while its
                # consumer stays connected. Only Completed proves that the
                # assistant transcript and run scope finished successfully.
                if shared and not completed:
                    from app.agent_runtime.service import RunInterrupted
                    raise RunInterrupted("Voice turn ended before durable completion")
                tail = stripper.flush()
                if tail:
                    _mark_yield()
                    yield _openai_delta(content=tail, chat_id=chat_id)
                yield _openai_done()
                _emit_perf("ok")
                return

            except Exception as exc:
                from app.agent_runtime.service import RunInterrupted
                if isinstance(exc, RunInterrupted):
                    _emit_perf("interrupted")
                    raise
                # Poisoned mid-run (e.g. a concurrent voice request cancelled a
                # tool call after our pre-flight check): repair and retry once,
                # but only if nothing streamed yet — a retry after spoken output
                # would repeat the sentence to the parent.
                if not shared and attempt == 1 and not yielded and not tool_started and is_dangling_tool_error(exc):
                    logger.warning(
                        "[parent-convai] dangling tool call mid-run — repairing and "
                        "retrying user=%s thread=%s", user_id, thread_id,
                    )
                    await repair_with_receipts(context, agent, config, repair_thread)
                    continue
                logger.exception(
                    "[parent-convai] stream error user=%s thread=%s", user_id, thread_id
                )
                _emit_perf("error")
                raise
    finally:
        # A barge-in is the MOST common way a voice turn ends, and it unwinds
        # this generator without reaching either exit above. Emitting only on
        # the clean exits would silently drop every interrupted turn out of the
        # latency histogram — leaving it measuring the turns nobody minded
        # waiting for. No-ops (perf_emitted) when the turn already reported.
        _emit_perf("interrupted")
