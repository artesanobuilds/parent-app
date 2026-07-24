"""
OpenAI-compatible /v1/chat/completions endpoint for ElevenLabs Conversational AI.

ElevenLabs calls this as a "Custom LLM" endpoint. We wrap our LangGraph kid agent
+ full 5-layer moderation pipeline, streaming tokens in OpenAI SSE format.

Auth: server-to-server shared secret via X-ElevenLabs-Secret header.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app import kid_agent as kid_agent_service
from app import moderation
from app import telemetry
from app.profiling import profiling_service
from app.prompt_synthesis import _age_band as _kid_age_band

logger = logging.getLogger(__name__)


def _crisis_push(storage: Any, user_id: str, kid_name: str, agent_id: str) -> Optional[str]:
    """Dispatch the crisis-lock push (no-op when APNs unconfigured); return an ISO
    timestamp for `parent_notified_at` when dispatched. Never raises."""
    from app import push
    if not push.is_enabled():
        return None
    try:
        push.send_crisis_push(storage=storage, user_id=user_id, kid_name=kid_name, agent_id=agent_id)
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        return None

router = APIRouter()

CONVAI_SECRET = os.getenv("ELEVENLABS_CONVAI_SECRET", "")


def _storage():
    from app.server import storage_backend
    return storage_backend


def _openai_delta(content: Optional[str] = None, tool_calls: Optional[list] = None, chat_id: str = "") -> str:
    delta: Dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    if tool_calls is not None:
        delta["tool_calls"] = tool_calls
    obj = {
        "id": f"chatcmpl-{chat_id}",
        "object": "chat.completion.chunk",
        "choices": [{"delta": delta, "index": 0, "finish_reason": None}],
    }
    return f"data: {json.dumps(obj)}\n\n"


def _openai_done() -> str:
    return "data: [DONE]\n\n"


def _end_call_tool_delta(chat_id: str) -> str:
    delta = {
        "tool_calls": [{
            "index": 0,
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": "end_call", "arguments": "{}"},
        }]
    }
    obj = {
        "id": f"chatcmpl-{chat_id}",
        "object": "chat.completion.chunk",
        "choices": [{"delta": delta, "index": 0, "finish_reason": "tool_calls"}],
    }
    return f"data: {json.dumps(obj)}\n\n"


# ── Voice-turn latency instrumentation ───────────────────────────────────────
# Shared by both Custom-LLM endpoints (the parent one imports these) so the two
# voice surfaces report the exact same numbers under the same metric names.

def _ms(mark: float) -> int:
    """Elapsed whole ms since a `time.monotonic()` mark. Monotonic, not wall
    clock — an NTP step mid-turn must not invent negative latency."""
    return int((time.monotonic() - mark) * 1000)


def _voice_perf_metrics(
    feature: str,
    *,
    repair_ms: Optional[int],
    model_ttft_ms: Optional[int],
    ttfb_ms: Optional[int],
    tool_turn: int,
    outcome: str,
) -> None:
    """OTel twin of the `[PERF][VOICE]` log line — logs are for forensics on one
    turn, these are for the p50/p95 trend.

    Dotted names follow the app/observability convention; Prometheus renders them
    as `voice_turn_ttfb_ms` / `voice_turn_model_ttft_ms` / `voice_turn_repair_ms`
    and the counter as `voice_turns_total`. Cardinality: 2 features × 2 tool_turn
    × 4 outcomes (ok / blocked / error / interrupted) = 16 series on the counter,
    2 each on the histograms.

    Defensive twice over — obs.count/observe are no-ops when OTel is unconfigured
    and swallow their own failures, and the whole body is wrapped besides. A
    metrics outage must never cost a parent or kid their turn."""
    try:
        from app import observability as obs

        if repair_ms is not None:
            obs.observe("voice.turn.repair_ms", float(repair_ms), feature=feature)
        if model_ttft_ms is not None:
            obs.observe("voice.turn.model_ttft_ms", float(model_ttft_ms), feature=feature)
        if ttfb_ms is not None:
            obs.observe("voice.turn.ttfb_ms", float(ttfb_ms), feature=feature)
        obs.count("voice.turns", feature=feature, tool_turn=tool_turn, outcome=outcome)
    except Exception:  # noqa: BLE001 — telemetry must never break a voice turn
        pass


async def _probe_stream():
    """Minimal valid OpenAI SSE stream for ElevenLabs' connection-test probe."""
    chat_id = "probe"
    yield _openai_delta(content="OK", chat_id=chat_id)
    yield _openai_done()


@router.post("/v1/chat/completions")
async def convai_chat_completions(
    request: Request,
    x_elevenlabs_secret: Optional[str] = Header(default=None, alias="X-ElevenLabs-Secret"),
    authorization: Optional[str] = Header(default=None),
):
    # ElevenLabs' Custom LLM "API key" field is sent as `Authorization: Bearer <secret>`.
    # Accept that as well as our legacy X-ElevenLabs-Secret header so either console
    # configuration path authenticates.
    bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
    presented = x_elevenlabs_secret or bearer
    if not CONVAI_SECRET or presented != CONVAI_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret")

    body = await request.json()
    messages = body.get("messages", [])
    raw_extra = body.get("elevenlabs_extra_body")
    extra = raw_extra or {}

    user_id = extra.get("user_id")
    kid_name = extra.get("kid_name")
    thread_id = extra.get("thread_id", "default")

    # ElevenLabs' "Test connection" probe (and any health check) sends a bare
    # OpenAI request with no elevenlabs_extra_body. Answer it with a valid stub
    # stream so the console marks the Custom LLM healthy — without spinning up an
    # agent or moderation. A body that *has* an extra_body but is missing the
    # session keys is a genuine misconfiguration, so that still 400s.
    if not user_id or not kid_name:
        if not raw_extra:
            return StreamingResponse(
                _probe_stream(), media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        raise HTTPException(status_code=400, detail="missing user_id or kid_name in elevenlabs_extra_body")

    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="no user message found")

    return StreamingResponse(
        _stream_response(user_id, kid_name, thread_id, last_user_msg),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_response(user_id: str, kid_name: str, thread_id: str, message: str):
    turn_started = time.monotonic()
    storage = _storage()
    chat_id = uuid.uuid4().hex[:12]

    from app.cost_logging import CostLoggingCallbackHandler, log_perf, new_workflow_id
    # ONE id for the whole voice turn (agent + moderation + the perf line), so
    # every [COST] line and the [PERF] line for this turn join on `workflow=`.
    voice_wf = new_workflow_id()

    # Turn timings. `model_ttft_ms` is when the model's first token reached US;
    # `ttfb_ms` is when the first delta reached ElevenLabs. The gap between them
    # is OUR buffering (moderation lookahead), i.e. the only part we can shrink.
    repair_ms: Optional[int] = None
    model_ttft_ms: Optional[int] = None
    ttfb_ms: Optional[int] = None
    chunks = 0
    tool_turn = 0
    perf_emitted = False

    def _mark_yield() -> None:
        """Call immediately before yielding a content delta to ElevenLabs."""
        nonlocal ttfb_ms, chunks
        if ttfb_ms is None:
            ttfb_ms = _ms(turn_started)
        chunks += 1

    def _emit_perf(outcome: str) -> None:
        """Exactly one [PERF][VOICE] line per turn, every exit path included —
        a turn that errored or got blocked is precisely the one worth timing."""
        nonlocal perf_emitted
        if perf_emitted:
            return
        perf_emitted = True
        log_perf(
            "VOICE", feature="kid_voice", workflow=voice_wf, session=thread_id,
            user=user_id, repair_ms=repair_ms, model_ttft_ms=model_ttft_ms,
            ttfb_ms=ttfb_ms, total_ms=_ms(turn_started), chunks=chunks,
            tool_turn=tool_turn,
        )
        _voice_perf_metrics(
            "kid_voice", repair_ms=repair_ms, model_ttft_ms=model_ttft_ms,
            ttfb_ms=ttfb_ms, tool_turn=tool_turn, outcome=outcome,
        )

    agent, config = kid_agent_service.get_kid_agent(user_id, kid_name)
    if not config.get("enabled"):
        _mark_yield()
        yield _openai_delta(content="I'm not ready to chat yet — your grown-up needs to set me up first.", chat_id=chat_id)
        yield _openai_done()
        _emit_perf("blocked")
        return

    agent_id = config["id"]
    invariants = config["invariants"]

    lock = storage.is_kid_agent_crisis_locked(agent_id)
    if lock is not None:
        frozen_msg = "Your grown-up needs to check in with you before we can chat again."
        _mark_yield()
        yield _openai_delta(content=frozen_msg, chat_id=chat_id)
        yield _end_call_tool_delta(chat_id)
        yield _openai_done()
        _emit_perf("blocked")
        return

    family = profiling_service.get_family_profile(user_id)
    kid_profile = (family.get("children") or {}).get(kid_name) or {}
    age_band = _kid_age_band(kid_profile.get("age"))

    pre = moderation.moderate_input(
        user_id=user_id, kid_name=kid_name, agent_id=agent_id,
        age_band=age_band, text=message,
        cost_workflow=voice_wf, cost_user=user_id,
    )

    user_msg_id = storage.append_kid_message(
        agent_id=agent_id, thread_id=thread_id, role="user", content=message,
        moderation_score=1.0 if pre.flagged else None,
        parent_flagged=pre.flagged,
    )

    if pre.flagged:
        if pre.suggested_action == "crisis_route":
            crisis_msg = (
                "I'm really glad you told me. This is something your "
                "grown-up needs to know — they want to help. I'm letting "
                "them know now."
            )
            storage.lock_kid_agent_for_crisis(
                agent_id=agent_id, user_id=user_id, kid_name=kid_name,
                category=pre.category, severity="crisis", reason=pre.reason,
            )
            moderation.kill_agent(agent_id)
            storage.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity="crisis",
                category=pre.category, action="crisis_routed",
                agent_id=agent_id, message_id=user_msg_id,
                details={"reason": pre.reason},
                parent_notified_at=_crisis_push(storage, user_id, kid_name, agent_id),
            )
            telemetry.alert_crisis(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                excerpt=message,
            )
            _mark_yield()
            yield _openai_delta(content=crisis_msg, chat_id=chat_id)
            yield _end_call_tool_delta(chat_id)
            yield _openai_done()
            _emit_perf("blocked")
            return
        else:
            redirect = "Hmm, let's try a different question — your grown-up will see this chat."
            storage.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity=pre.severity,
                category=pre.category, action="blocked_input",
                agent_id=agent_id, message_id=user_msg_id,
                details={"reason": pre.reason},
            )
            _mark_yield()
            yield _openai_delta(content=redirect, chat_id=chat_id)
            yield _openai_done()
            _emit_perf("blocked")
            return

    memory_key = f"kid:{user_id}:{kid_name}:{thread_id}"
    _voice_cost = CostLoggingCallbackHandler(
        feature="kid_voice", workflow=voice_wf, session=thread_id, user=user_id
    )
    config_lg = {"configurable": {"thread_id": memory_key}, "callbacks": [_voice_cost]}

    # Self-heal a thread poisoned by a cancelled tool call (see
    # app/thread_repair.py) before running the turn.
    from app.thread_repair import repair_thread
    repair_started = time.monotonic()
    await repair_thread(agent, config_lg)
    repair_ms = _ms(repair_started)

    sm = moderation.StreamingModerator(
        user_id=user_id, kid_name=kid_name, agent_id=agent_id, age_band=age_band,
        cost_workflow=voice_wf, cost_user=user_id,
    )
    assistant_buffer = ""
    block_handled = False
    # Barge-in aborts the HTTP request, which throws GeneratorExit into this
    # generator mid-loop — so the post-loop append below never runs and the kid's
    # DURABLE history silently loses the turn they just heard half of. `persisted`
    # lets the finally: at the bottom write it exactly once. See that block.
    persisted = False

    def _apply_block_side_effects():
        nonlocal block_handled
        if block_handled or not sm.block_reason:
            return
        block_handled = True
        if sm.block_reason.severity == "crisis":
            storage.lock_kid_agent_for_crisis(
                agent_id=agent_id, user_id=user_id, kid_name=kid_name,
                category=sm.block_reason.category, severity="crisis",
                reason=f"output: {sm.block_reason.reason}",
            )
            moderation.kill_agent(agent_id)
            storage.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity="crisis",
                category=sm.block_reason.category, action="crisis_routed",
                agent_id=agent_id, message_id=user_msg_id,
                details={"side": "output"},
                parent_notified_at=_crisis_push(storage, user_id, kid_name, agent_id),
            )
            telemetry.alert_crisis(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                excerpt="[redacted-crisis-output]",
            )
        else:
            storage.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity=sm.block_reason.severity,
                category=sm.block_reason.category, action="blocked_output",
                agent_id=agent_id, message_id=user_msg_id,
                details={"reason": sm.block_reason.reason},
            )

    try:
        # version="v2" is the cheaper event API — v1 builds a much heavier event
        # payload per token, which is pure overhead on a voice hot path where
        # every ms is audible. The two filters we use (`event["event"]` kind and
        # `data.chunk.content`) are identical across versions.
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config_lg,
            version="v2",
        ):
            kind = event["event"]
            if kind == "on_tool_start" and model_ttft_ms is None:
                # A tool ran before the first spoken token — that turn's latency
                # belongs in its own bucket, not the plain-answer distribution.
                tool_turn = 1
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                # In v2 a chunk's content can be a LIST of content blocks (tool-call
                # deltas), not a str. Concatenating that into the buffer or feeding
                # it to the moderator would blow up mid-turn, so skip anything that
                # isn't spoken text — the tool result comes back as a later chunk.
                if not content or not isinstance(content, str):
                    continue
                if model_ttft_ms is None:
                    model_ttft_ms = _ms(turn_started)  # before moderation buffering
                assistant_buffer += content
                for safe in sm.feed(content):
                    _mark_yield()
                    yield _openai_delta(content=safe, chat_id=chat_id)
                if sm.state.value == "blocked":
                    _apply_block_side_effects()
                    _mark_yield()
                    yield _openai_delta(content=sm.replacement_message(), chat_id=chat_id)
                    yield _end_call_tool_delta(chat_id)
                    break

        for chunk in sm.finalize():
            _mark_yield()
            yield _openai_delta(content=chunk, chat_id=chat_id)

        if sm.state.value == "blocked" and sm.block_reason:
            already = block_handled
            _apply_block_side_effects()
            if not already:
                _mark_yield()
                yield _openai_delta(content=sm.replacement_message(), chat_id=chat_id)
                yield _end_call_tool_delta(chat_id)
            storage.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.replacement_message(), parent_flagged=True,
            )
            persisted = True
        elif assistant_buffer:
            reply_id = str(uuid.uuid4())
            storage.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.assembled_output or assistant_buffer,
                message_id=reply_id,
            )
            persisted = True

        yield _openai_done()
        _emit_perf("blocked" if sm.state.value == "blocked" else "ok")

    except Exception as e:
        logger.exception(
            "[convai] stream error user=%s kid=%s thread=%s", user_id, kid_name, thread_id
        )
        _mark_yield()
        yield _openai_delta(content="Something went wrong. Let's try again.", chat_id=chat_id)
        yield _openai_done()
        _emit_perf("error")

    finally:
        # Interrupted-turn durability. A barge-in (or any client abort) closes this
        # generator, so neither branch above ran — yet the kid HEARD part of the
        # reply and the parent will look for it in the transcript. Persist what we
        # actually generated, preferring the moderator's assembled/safe text over
        # the raw buffer so nothing unreviewed lands in durable history.
        #
        # Deliberately minimal: a synchronous storage append and nothing else. No
        # crisis side effects (lock / push / end_call) fire here — those stay in
        # _apply_block_side_effects on the live path, because a cancelled request
        # is not the place to lock an agent or wake a parent's phone. A blocked
        # turn writes nothing: the replacement message was never spoken.
        if not persisted and assistant_buffer and sm.state.value != "blocked":
            try:
                storage.append_kid_message(
                    agent_id=agent_id, thread_id=thread_id, role="assistant",
                    content=sm.assembled_output or assistant_buffer,
                    message_id=str(uuid.uuid4()),
                )
            except Exception:  # noqa: BLE001 — best-effort; never mask the real exit
                logger.warning(
                    "[convai] interrupted-turn persist failed user=%s kid=%s thread=%s",
                    user_id, kid_name, thread_id,
                )
        # A barge-in is the MOST common way a voice turn ends, and it reaches
        # here without passing either branch above. Emitting only on the clean
        # exits would silently drop every interrupted turn out of the latency
        # histogram — leaving it measuring the turns nobody minded waiting for.
        # No-ops (perf_emitted) when the turn already reported.
        _emit_perf("interrupted")
