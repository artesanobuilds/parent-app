"""
Kid runtime agent. Built per (user_id, kid_name) from the saved KidAgentConfig.

Architecture:
- Saved invariants remain the parent-approved source for personality, boundaries,
  goals and tools. Runtime reads rebuild the deterministic prompt from those
  invariants, the current child profile, the current soul and the surface policy.
- Effective input fingerprints invalidate cached graphs without re-synthesizing
  or writing the reviewed configuration.
- Defaults to gpt-5.2 today. The plan calls for Haiku 4.5 for cost/latency;
  swapping requires adding `langchain-anthropic` to requirements and using
  ChatAnthropic here. Tracked in roadmap.
"""

from __future__ import annotations

from app.agent_runtime.cache import AgentCache

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent

from app.checkpointing import checkpointer as _kid_checkpointer
from app.profiling import profiling_service
from app.prompt_synthesis import (
    SynthesisResult,
    build_system_prompt,
    synthesize,
)

logger = logging.getLogger(__name__)


# ── Configuration ────────────────────────────────────────────────────

# Plan calls for Haiku 4.5 here. Pinned to OpenAI for now to avoid a new
# dependency mid-feature; swap-target tracked in roadmap.md.
KID_RUNTIME_MODEL = os.getenv("KID_RUNTIME_MODEL", "gpt-5.2")

# Kid threads share the ONE durable SQLite checkpointer with the parent and
# onboarding agents (app/checkpointing.py) — imported above under the name this
# module's `create_agent` call already used, so the call site is unchanged. Kid
# thread ids are `kid:{user}:{kid}:{thread}`; the delete cascade sweeps them by
# that prefix.


# ── Cache ────────────────────────────────────────────────────────────

# Keyed by (user_id, kid_name); value carries the effective input fingerprint.
# Switching text/voice replaces this slot; tenant invalidation stays unchanged.
_kid_agent_cache = AgentCache()


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


def _effective_prompt_inputs(user_id: str, kid_name: str, config: Dict[str, Any],
                             surface: str):
    from app.voice_policy import is_voice_surface
    voice = is_voice_surface(surface)
    family = profiling_service.get_family_profile(user_id) or {}
    kid_profile = (family.get("children") or {}).get(kid_name) or {"name": kid_name}
    prompt = build_system_prompt(
        kid_profile=kid_profile, invariants=config.get("invariants") or {},
        # Keep legacy text-mode configurations intact; a voice request always
        # activates spoken guidance regardless of their saved voice_mode bit.
        voice_mode=True if voice else None,
    )
    return prompt, kid_profile


def build_effective_prompt(user_id: str, kid_name: str, config: Dict[str, Any],
                           *, surface: str = "text") -> str:
    """Read current context without changing the parent's reviewed configuration."""
    prompt, _ = _effective_prompt_inputs(user_id, kid_name, config, surface)
    return prompt


def get_kid_agent(user_id: str, kid_name: str, *, surface: str = "text"):
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

    prompt, kid_profile = _effective_prompt_inputs(user_id, kid_name, config, surface)
    # Hash the effective prompt as well as inputs: soul/policy changes and
    # profile changes invalidate an unchanged stored configuration hash.
    fingerprint = hashlib.sha256(json.dumps({
        "profile": kid_profile, "invariants": config.get("invariants") or {},
        "prompt": prompt, "surface": surface, "model": KID_RUNTIME_MODEL,
    }, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    cached = _kid_agent_cache.get(_cache_key(user_id, kid_name))
    if cached and cached.get("content_hash") == fingerprint:
        return cached["agent"], config

    agent_executor = create_agent(
        model=ChatOpenAI(model=KID_RUNTIME_MODEL, stream_usage=True),
        tools=_wire_tools(config["invariants"]),
        checkpointer=_kid_checkpointer,
        system_prompt=prompt,
    )
    _kid_agent_cache[_cache_key(user_id, kid_name)] = {
        "agent": agent_executor,
        "content_hash": fingerprint,
    }
    logger.info(
        "[kid_agent] built agent for user=%s kid=%s v%d hash=%s",
        user_id, kid_name, config["version"], fingerprint,
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
