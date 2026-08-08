"""Chief-of-Staff agent — MERGED into the single parent agent.

There is no separate Chief-of-Staff graph any more. Coach and Chief-of-Staff
are one agent harness for the whole parent experience: one model, one
checkpointer, one per-parent thread, one system prompt with both role halves
(``app/agent.py``; the planning half of the prompt lives in
``app/cos/prompt.py``, the planning tools still in ``app/cos/tools.py``).

This module stays as the compatibility seam so `/cos/chat`, the golden set and
anything else that asks for "the COS agent" keep working — they now get the
merged agent, which is the point.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.cos.prompt import COS_ROLE_SECTIONS

logger = logging.getLogger(__name__)

# Kept for readers who grep for the old name; the text moved to app/cos/prompt.
_ROLE_PREAMBLE = COS_ROLE_SECTIONS


def get_cos_agent(user_id: str = "0"):
    """The merged parent agent. Identical object to ``app.agent.get_agent``."""
    from app.agent import get_agent

    return get_agent(user_id)


def cos_thread_key(user_id: str, thread_id: str = "default") -> str:
    """The LangGraph thread `/cos/chat` runs on — the SAME merged per-parent
    text thread the coach uses, so a plan and a coaching conversation are one
    memory. The client's ``thread_id`` still scopes the stored transcript
    (`cos_messages`), just not the agent's thread."""
    from app.agent import thread_key

    return thread_key(user_id, "cos", thread_id)


# Legacy cache handle — the merged agent's cache lives in app.agent.
_cos_agent_cache: Dict[str, Dict[str, Any]] = {}
