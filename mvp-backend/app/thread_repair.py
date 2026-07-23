"""
Self-healing repair for LangGraph agent threads with dangling tool calls.

An agent turn can be cancelled mid-tool-call: ElevenLabs aborts its Custom-LLM
request on barge-in or slow first token, a client disconnects, a worker dies.
When the cancel lands after the model's tool_calls message is checkpointed but
before the tool's result message is, the thread is left with a DANGLING tool
call — and OpenAI then rejects the ENTIRE history on every later turn
("An assistant message with 'tool_calls' must be followed by tool messages
responding to each 'tool_call_id'"). Nothing ever removes the bad message, so
without repair the thread is poisoned until the process restarts (this took
out parent voice for a beta user from 2026-07-20 to 07-22).

`repair_thread(agent, config)` runs before every agent turn on every surface
(parent voice, kid voice, text chat, onboarding chat): it scans the thread's
checkpointed messages, strips tool calls that never received a ToolMessage,
and drops ToolMessages that answer a tool call that no longer exists. The
pure planning step lives in `plan_repairs` so tests can cover the matrix
without a checkpointer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, RemoveMessage, ToolMessage

logger = logging.getLogger(__name__)


def is_dangling_tool_error(exc: BaseException) -> bool:
    """True when an exception is OpenAI's rejection of a history whose tool
    calls lack response messages — the one failure repair + retry can fix."""
    text = str(exc)
    return "tool_call" in text and (
        "did not have response messages" in text
        or "must be followed by tool messages" in text
    )


def _call_ids(message: AIMessage) -> List[str]:
    """All tool-call ids an AIMessage would send to OpenAI (valid + invalid)."""
    ids = [tc.get("id") for tc in (message.tool_calls or [])]
    ids += [tc.get("id") for tc in (message.invalid_tool_calls or [])]
    return [i for i in ids if i]


def plan_repairs(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    """Return the add_messages updates (replacements by id / RemoveMessage)
    that make the history valid for OpenAI. Empty list = healthy thread."""
    answered = {
        m.tool_call_id for m in messages
        if isinstance(m, ToolMessage) and m.tool_call_id
    }
    known: set = set()
    for m in messages:
        if isinstance(m, AIMessage):
            known.update(_call_ids(m))

    updates: List[BaseMessage] = []
    for m in messages:
        # A tool result whose originating call is gone is itself invalid.
        if isinstance(m, ToolMessage) and m.tool_call_id and m.tool_call_id not in known:
            if m.id:
                updates.append(RemoveMessage(id=m.id))
            continue
        if not isinstance(m, AIMessage):
            continue
        ids = _call_ids(m)
        if not ids or all(i in answered for i in ids):
            continue
        if m.id is None:
            continue  # can't target it; add_messages assigns ids, so unreachable
        keep = [tc for tc in (m.tool_calls or []) if tc.get("id") in answered]
        if keep or m.content:
            # Replace in place (same id): keep the prose and any answered
            # calls, drop the dangling ones. Fresh construction on purpose —
            # additional_kwargs may carry the raw OpenAI tool_calls too.
            updates.append(AIMessage(id=m.id, content=m.content, tool_calls=keep))
        else:
            # Pure tool-call message with no answers: the turn never happened
            # as far as the user knows — delete it.
            updates.append(RemoveMessage(id=m.id))
    return updates


async def repair_thread(agent: Any, config: Dict[str, Any]) -> int:
    """Scan + fix one thread's checkpointed history. Returns the number of
    repairs applied (0 = healthy). Never raises — a failed repair must not
    take down the turn it was trying to protect."""
    thread = config.get("configurable", {}).get("thread_id", "?")
    try:
        state = await agent.aget_state(config)
        messages = (state.values or {}).get("messages", []) if state else []
        if not messages:
            return 0
        updates = plan_repairs(messages)
        if not updates:
            return 0
        # aupdate_state needs an unambiguous writer node; which one is
        # ambiguous depends on where the interrupted run stopped. "model" is
        # the message-writing node in every create_agent graph here.
        try:
            await agent.aupdate_state(config, {"messages": updates})
        except Exception:
            await agent.aupdate_state(config, {"messages": updates}, as_node="model")
        logger.warning(
            "[thread-repair] healed thread=%s: %d dangling-tool-call fix(es)",
            thread, len(updates),
        )
        return len(updates)
    except Exception:
        logger.exception("[thread-repair] repair failed thread=%s", thread)
        return 0
