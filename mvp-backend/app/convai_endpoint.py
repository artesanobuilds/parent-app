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
    storage = _storage()
    chat_id = uuid.uuid4().hex[:12]

    agent, config = kid_agent_service.get_kid_agent(user_id, kid_name)
    if not config.get("enabled"):
        yield _openai_delta(content="I'm not ready to chat yet — your grown-up needs to set me up first.", chat_id=chat_id)
        yield _openai_done()
        return

    agent_id = config["id"]
    invariants = config["invariants"]

    lock = storage.is_kid_agent_crisis_locked(agent_id)
    if lock is not None:
        frozen_msg = "Your grown-up needs to check in with you before we can chat again."
        yield _openai_delta(content=frozen_msg, chat_id=chat_id)
        yield _end_call_tool_delta(chat_id)
        yield _openai_done()
        return

    family = profiling_service.get_family_profile(user_id)
    kid_profile = (family.get("children") or {}).get(kid_name) or {}
    age_band = _kid_age_band(kid_profile.get("age"))

    from app.cost_logging import CostLoggingCallbackHandler, new_workflow_id
    voice_wf = new_workflow_id()  # one id for the whole voice turn (agent + moderation)

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
            yield _openai_delta(content=crisis_msg, chat_id=chat_id)
            yield _end_call_tool_delta(chat_id)
            yield _openai_done()
            return
        else:
            redirect = "Hmm, let's try a different question — your grown-up will see this chat."
            storage.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity=pre.severity,
                category=pre.category, action="blocked_input",
                agent_id=agent_id, message_id=user_msg_id,
                details={"reason": pre.reason},
            )
            yield _openai_delta(content=redirect, chat_id=chat_id)
            yield _openai_done()
            return

    memory_key = f"kid:{user_id}:{kid_name}:{thread_id}"
    _voice_cost = CostLoggingCallbackHandler(
        feature="kid_voice", workflow=voice_wf, session=thread_id, user=user_id
    )
    config_lg = {"configurable": {"thread_id": memory_key}, "callbacks": [_voice_cost]}

    sm = moderation.StreamingModerator(
        user_id=user_id, kid_name=kid_name, agent_id=agent_id, age_band=age_band,
        cost_workflow=voice_wf, cost_user=user_id,
    )
    assistant_buffer = ""
    block_handled = False

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
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config_lg,
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if not content:
                    continue
                assistant_buffer += content
                for safe in sm.feed(content):
                    yield _openai_delta(content=safe, chat_id=chat_id)
                if sm.state.value == "blocked":
                    _apply_block_side_effects()
                    yield _openai_delta(content=sm.replacement_message(), chat_id=chat_id)
                    yield _end_call_tool_delta(chat_id)
                    break

        for chunk in sm.finalize():
            yield _openai_delta(content=chunk, chat_id=chat_id)

        if sm.state.value == "blocked" and sm.block_reason:
            already = block_handled
            _apply_block_side_effects()
            if not already:
                yield _openai_delta(content=sm.replacement_message(), chat_id=chat_id)
                yield _end_call_tool_delta(chat_id)
            storage.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.replacement_message(), parent_flagged=True,
            )
        elif assistant_buffer:
            reply_id = str(uuid.uuid4())
            storage.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.assembled_output or assistant_buffer,
                message_id=reply_id,
            )

        yield _openai_done()

    except Exception as e:
        logger.exception("[convai] stream error")
        yield _openai_delta(content="Something went wrong. Let's try again.", chat_id=chat_id)
        yield _openai_done()
