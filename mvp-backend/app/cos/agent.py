"""Chief-of-Staff agent — kids'-activity planning.

This agent is FULLY isolated from the parent coach in ``app/agent.py``: its own
``ChatOpenAI`` model, its own ``MemorySaver`` checkpointer, and its own per-user
cache. A bug here can never reach the live coach.

The system prompt is kept STABLE (role preamble + pruned family profile) so it
caches well. Mutable plan state (tracked activities, calendar, to-dos, gaps) is
NEVER baked into the prompt — the agent reads it at runtime via the
``GetPlanSnapshot`` / ``SearchActivities`` tools.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from dotenv import load_dotenv

from app.profiling import profiling_service
from app.cos.tools import build_cos_tools

logger = logging.getLogger(__name__)

load_dotenv()

# Own model — COS_MODEL overrides, else the shared default. Separate instance
# from app.agent.llm on purpose.
_cos_model_name = os.getenv("COS_MODEL", os.getenv("OPENAI_MODEL_NAME", "gpt-5.2"))
_cos_llm = ChatOpenAI(model=_cos_model_name, stream_usage=True)

# Own checkpointer — must NOT be shared with the parent coach.
_cos_checkpointer = MemorySaver()

_ROLE_PREAMBLE = """\
You are the parent's Chief of Staff for coordinating their kids' camps, classes,
and activities. You run the logistics so the parent doesn't have to hold it all
in their head. Your responsibilities:

- Track camps/activities, keeping PENDING vs CONFIRMED status explicit at all times.
- Build a week-by-week calendar of who is where.
- Maintain a running to-do / follow-ups list (signups, payments, emails to send).
- Assign caregiver logistics (dropoff/pickup/transport) and surface COVERAGE GAPS
  — any week or slot with no adult covering a kid.
- Flag TIME CONFLICTS (a camp overlapping a recurring appointment like therapy)
  and AGE-ELIGIBILITY issues before the parent commits.
- Keep a running COST picture (confirmed total + what's still TBD).
- Draft emails to organizers when asked — but NEVER send them. You hand the
  parent a draft to review and send themselves (human-in-the-loop).

Operating rules:
- ALWAYS call GetPlanSnapshot before answering "what's my plan / what's left /
  are we covered" questions — it is your source of truth for current state.
- Use SearchActivities to look up already-discovered candidates.
- Record decisions by calling the appropriate tool (TrackActivity, AddToCalendar,
  AddTodo, AssignLogistics, ...). Don't just describe an action — take it.
- Be concise and action-oriented. Confirm what you did and surface the next gap.
"""


def _prune_empty(value: Any) -> Any:
    """Recursively prune empty/None values to keep the prompt lean (mirrors agent.py)."""
    if isinstance(value, dict):
        pruned = {k: _prune_empty(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v not in (None, [], {}, "")}
    if isinstance(value, list):
        pruned_list = [_prune_empty(v) for v in value]
        return [v for v in pruned_list if v not in (None, [], {}, "")]
    return value


def _build_cos_system_prompt(profile_context: str | None) -> str:
    profile_section = ""
    if profile_context:
        profile_section = f"""

Family profile (use to personalize planning; never dump as raw data):
{profile_context}
"""
    return f"{_ROLE_PREAMBLE}{profile_section}"


_cos_agent_cache: Dict[str, Dict[str, Any]] = {}


def get_cos_agent(user_id: str = "0"):
    """Return a cached Chief-of-Staff agent for ``user_id``.

    Cached by user; invalidated when the pruned profile context string changes
    (same approach as ``app/agent.get_agent``).
    """
    raw_profile = profiling_service.get_family_profile(user_id)
    pruned_profile = _prune_empty(raw_profile)
    profile_context = (
        json.dumps(pruned_profile, ensure_ascii=False, indent=2)
        if pruned_profile
        else None
    )

    cached = _cos_agent_cache.get(user_id)
    if cached and cached.get("profile") == profile_context:
        return cached["agent"]

    agent_executor = create_agent(
        model=_cos_llm,
        tools=build_cos_tools(user_id),
        checkpointer=_cos_checkpointer,
        system_prompt=_build_cos_system_prompt(profile_context),
    )
    _cos_agent_cache[user_id] = {"agent": agent_executor, "profile": profile_context}
    return agent_executor
