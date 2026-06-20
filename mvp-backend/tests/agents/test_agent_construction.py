"""
Construction-level guard for the parent coach and kid runtime agents.

Both build via `langchain.agents.create_agent`. The single biggest risk of the
deepagents-driven stack bump (langchain 1.2->1.3+, langchain-core 1.2.5->1.4.7+,
langgraph->1.1) is that `create_agent`'s signature or return type drifts. These
tests build each agent with the LLM key stubbed (conftest) and storage/profile
mocked, and assert the result is an invokable graph — catching import or
return-type breakage offline, before the requirements.txt change is committed.
"""
from __future__ import annotations

import sys
import types

import pytest


def _assert_invokable_graph(agent) -> None:
    # create_agent returns a compiled LangGraph graph. We don't run it (no
    # network); we just assert the runtime surface the server depends on exists.
    for attr in ("astream_events", "ainvoke", "invoke"):
        assert hasattr(agent, attr), f"built agent is missing {attr!r}"


def test_parent_agent_builds_and_caches(monkeypatch):
    import app.agent as agent_mod

    # No profile -> no profile_context; avoids any storage dependency.
    monkeypatch.setattr(agent_mod.profiling_service, "get_family_profile", lambda u: {})
    # The system prompt pulls the content catalog, which needs the content
    # service initialized; stub it so this stays a pure construction test.
    monkeypatch.setattr(agent_mod, "content_catalog_for_prompt", lambda: "")
    agent_mod._agent_cache.clear()

    a1 = agent_mod.get_agent("user-1")
    _assert_invokable_graph(a1)

    # Same user + unchanged profile must return the cached instance.
    a2 = agent_mod.get_agent("user-1")
    assert a1 is a2, "get_agent should return the cached agent when profile is unchanged"


def test_kid_agent_builds_from_stored_config(monkeypatch):
    """get_kid_agent late-imports `app.server.storage_backend`; stub it so we
    build straight from a stored config without synthesis or the network."""
    import app.kid_agent as kid_mod

    fake_config = {
        "invariants": {"tools_enabled": {"web_search": False}},
        "system_prompt": "You are a friendly test agent for a kid named Ceiba.",
        "content_hash": "deadbeefdeadbeef",
        "version": 1,
    }

    fake_server = types.ModuleType("app.server")
    fake_server.storage_backend = types.SimpleNamespace(
        get_kid_agent_config=lambda user_id, kid_name: fake_config
    )
    monkeypatch.setitem(sys.modules, "app.server", fake_server)
    kid_mod._kid_agent_cache.clear()

    agent, config = kid_mod.get_kid_agent("user-1", "Ceiba")
    _assert_invokable_graph(agent)
    assert config["content_hash"] == "deadbeefdeadbeef"

    # Unchanged content_hash -> cached instance.
    agent2, _ = kid_mod.get_kid_agent("user-1", "Ceiba")
    assert agent is agent2, "kid agent should be cached by content_hash"


def test_kid_agent_wires_web_search_tool_when_enabled(monkeypatch):
    """Tool wiring is part of the construction contract: an enabled flag must
    produce exactly one tool; disabled produces none."""
    import app.kid_agent as kid_mod

    assert kid_mod._wire_tools({"tools_enabled": {}}) == []
    wired = kid_mod._wire_tools({"tools_enabled": {"web_search": True}})
    assert len(wired) == 1, "web_search enabled should wire exactly one tool"
