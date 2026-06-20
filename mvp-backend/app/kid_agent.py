"""
Kid runtime agent. Built per (user_id, kid_name) from the saved KidAgentConfig.

Architecture:
- KidAgentConfig (in DuckDB) is the source of truth for what tools are wired,
  what's blocked, what the personality is. The system_prompt embedded in that
  config is what the LLM actually sees.
- Cache key is the config's content_hash, so any drift in config / kid profile /
  parent profile / soul_kid.md / synthesis version invalidates the cache.
- Defaults to gpt-5.2 today. The plan calls for Haiku 4.5 for cost/latency;
  swapping requires adding `langchain-anthropic` to requirements and using
  ChatAnthropic here. Tracked in roadmap.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from app.profiling import profiling_service
from app.prompt_synthesis import (
    SynthesisResult,
    build_system_prompt,
    compute_content_hash,
    SYNTHESIS_VERSION,
    _soul_kid_content,
    synthesize,
)

logger = logging.getLogger(__name__)


# ── Configuration ────────────────────────────────────────────────────

# Plan calls for Haiku 4.5 here. Pinned to OpenAI for now to avoid a new
# dependency mid-feature; swap-target tracked in roadmap.md.
KID_RUNTIME_MODEL = os.getenv("KID_RUNTIME_MODEL", "gpt-5.2")

# Shared in-memory checkpointer for kid threads. Same caveat as the parent
# agent: this is process-local; production needs a SQL/DuckDB-backed
# checkpointer (also tracked in plan Phase 0).
_kid_checkpointer = MemorySaver()


# ── Cache ────────────────────────────────────────────────────────────

# Keyed by (user_id, kid_name); value carries content_hash so we invalidate
# whenever anything that affects the runtime prompt has changed.
_kid_agent_cache: Dict[str, Dict[str, Any]] = {}


def _cache_key(user_id: str, kid_name: str) -> str:
    return f"{user_id}::{kid_name}"


# ── Tool wiring ──────────────────────────────────────────────────────


def _wire_tools(invariants: Dict[str, Any]) -> List[Any]:
    """
    Build the tool list from the parent's enabled flags. Only the tools listed
    here are wired into the runtime agent. Disabled tools are not just hidden
    in the system prompt — they don't exist as far as the model is concerned.
    """
    enabled = invariants.get("tools_enabled") or {}
    tools: List[Any] = []

    if enabled.get("web_search"):
        tools.append(TavilySearch(max_results=2))

    # image_upload, image_generation, math_solver, reading_helper are
    # placeholders for v1. They'll be added as @tool functions in their own
    # modules when the corresponding UI affordances ship.

    return tools


# ── Public API ───────────────────────────────────────────────────────


def get_kid_agent(user_id: str, kid_name: str):
    """
    Return a cached LangGraph agent for this kid. Lazily synthesizes a default
    config (via prompt_synthesis.synthesize) if one doesn't exist yet — that's
    how a kid with a profile but no parent review still has *something* to
    point the review screen at.

    Imports the storage module locally to avoid a circular import at load time.
    """
    from app.server import storage_backend as storage  # late import; module-level singleton

    config = storage.get_kid_agent_config(user_id, kid_name)

    if config is None:
        # First touch — auto-generate a default config from the kid profile.
        # Marked enabled=False so the parent must review before a kid can talk to it.
        config = _bootstrap_default_config(user_id, kid_name, storage)

    cached = _kid_agent_cache.get(_cache_key(user_id, kid_name))
    if cached and cached.get("content_hash") == config["content_hash"]:
        return cached["agent"], config

    agent_executor = create_agent(
        model=ChatOpenAI(model=KID_RUNTIME_MODEL, stream_usage=True),
        tools=_wire_tools(config["invariants"]),
        checkpointer=_kid_checkpointer,
        system_prompt=config["system_prompt"],
    )
    _kid_agent_cache[_cache_key(user_id, kid_name)] = {
        "agent": agent_executor,
        "content_hash": config["content_hash"],
    }
    logger.info(
        "[kid_agent] built agent for user=%s kid=%s v%d hash=%s",
        user_id, kid_name, config["version"], config["content_hash"],
    )
    return agent_executor, config


def upsert_kid_agent_config(
    *,
    user_id: str,
    kid_name: str,
    brief: str,
    expected_version: Optional[int] = None,
    enable: bool = False,
) -> Dict[str, Any]:
    """
    Re-synthesize and persist a new config row for (user_id, kid_name).
    expected_version supports optimistic concurrency; pass None on first write.
    Returns the new persisted config.
    """
    from app.server import storage_backend as storage

    family = profiling_service.get_family_profile(user_id)
    children = family.get("children") or {}
    kid_profile = children.get(kid_name) or {"name": kid_name}

    prior = storage.get_kid_agent_config(user_id, kid_name)
    parent_summary = family.get("parent")

    result: SynthesisResult = synthesize(
        brief=brief,
        kid_profile=kid_profile,
        parent_profile_summary=parent_summary,
        prior_config=prior,
        cost_user=user_id,
    )

    saved = storage.save_kid_agent_config(
        user_id=user_id,
        kid_name=kid_name,
        invariants=result.invariants,
        free_text_brief=brief,
        system_prompt=result.system_prompt,
        content_hash=result.content_hash,
        model=result.model,
        enabled=enable,
        expected_version=expected_version,
    )

    # Invalidate cache for this kid; next get_kid_agent will rebuild.
    _kid_agent_cache.pop(_cache_key(user_id, kid_name), None)
    return saved


def invalidate_kid_agent(user_id: str, kid_name: str) -> None:
    _kid_agent_cache.pop(_cache_key(user_id, kid_name), None)


def invalidate_user(user_id: str) -> None:
    """Drop every cached agent for this user_id (used after family delete)."""
    prefix = f"{user_id}::"
    for k in list(_kid_agent_cache.keys()):
        if k.startswith(prefix):
            _kid_agent_cache.pop(k, None)


# ── Internals ────────────────────────────────────────────────────────


def _bootstrap_default_config(
    user_id: str,
    kid_name: str,
    storage,
) -> Dict[str, Any]:
    """
    Create a sensible default config for a kid we've never reviewed. Marked
    enabled=False so the parent must explicitly approve via the review screen
    before the kid can actually talk to it.
    """
    family = profiling_service.get_family_profile(user_id)
    children = family.get("children") or {}
    kid_profile = children.get(kid_name) or {"name": kid_name}
    parent_summary = family.get("parent")

    result = synthesize(
        brief="",  # auto-gen: no parent input yet
        kid_profile=kid_profile,
        parent_profile_summary=parent_summary,
        prior_config=None,
        cost_user=user_id,
    )

    return storage.save_kid_agent_config(
        user_id=user_id,
        kid_name=kid_name,
        invariants=result.invariants,
        free_text_brief="",
        system_prompt=result.system_prompt,
        content_hash=result.content_hash,
        model=result.model,
        enabled=False,
        expected_version=None,
    )
