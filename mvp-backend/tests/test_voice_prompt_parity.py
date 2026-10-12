"""Offline proof that voice policy reaches actual graph construction."""
from copy import deepcopy
from types import SimpleNamespace
import sys

import pytest

from app.agent_runtime.cache import AgentCache


@pytest.fixture
def kid_factory(monkeypatch):
    from app import kid_agent as kid
    config = {
        "version": 2, "content_hash": "stored-review-hash", "system_prompt": "OLD PROFILE",
        "enabled": True, "invariants": {
            "agent_display_name": "Nova", "personality_description": "Patient and curious.",
            "goals": ["practice taking turns"], "topics_blocked": ["violent games"],
            "topics_allowed": ["dinosaurs"], "tools_enabled": {"web_search": False},
            "voice_mode": False,
        },
    }
    family = {"parent": {"name": "PRIVATE PARENT CONTEXT"}, "children": {
        "Sam": {"name": "Sam", "age": 6, "interests": ["dinosaurs"]},
    }}
    storage = SimpleNamespace(get_kid_agent_config=lambda uid, name: config)
    monkeypatch.setitem(sys.modules, "app.server", SimpleNamespace(storage_backend=storage))
    monkeypatch.setattr(kid, "profiling_service", SimpleNamespace(get_family_profile=lambda uid: deepcopy(family)))
    monkeypatch.setattr(kid, "_kid_agent_cache", AgentCache(4))
    monkeypatch.setattr(kid, "ChatOpenAI", lambda **kwargs: kwargs)
    monkeypatch.setattr(kid, "create_agent", lambda **kwargs: SimpleNamespace(**kwargs))
    monkeypatch.setattr(kid, "synthesize", lambda **kwargs: pytest.fail("runtime must not re-synthesize"))
    return kid, config, family


def sealed(prompt):
    return prompt.split("<non_negotiable>", 1)[1].split("</non_negotiable>", 1)[0]


def test_kid_voice_graph_has_policy_and_keeps_parent_boundaries(kid_factory):
    kid, config, family = kid_factory
    saved = deepcopy(config)
    text, returned = kid.get_kid_agent("family", "Sam")
    voice, _ = kid.get_kid_agent("family", "Sam", surface="voice")
    assert "## Voice mode" not in text.system_prompt
    assert "## Voice mode" in voice.system_prompt
    assert "one question at a time" in voice.system_prompt
    assert sealed(text.system_prompt) == sealed(voice.system_prompt)
    assert "violent games" in voice.system_prompt
    assert "practice taking turns" in voice.system_prompt
    assert "PRIVATE PARENT CONTEXT" not in voice.system_prompt
    assert text.tools == voice.tools == []
    assert voice.checkpointer is text.checkpointer
    assert returned is config and config == saved
    again, _ = kid.get_kid_agent("family", "Sam", surface="voice")
    assert again is voice
    new_text, _ = kid.get_kid_agent("family", "Sam")
    assert "## Voice mode" not in new_text.system_prompt


def test_current_child_profile_invalidates_unchanged_review_hash(kid_factory):
    kid, config, family = kid_factory
    old, _ = kid.get_kid_agent("family", "Sam", surface="voice")
    family["children"]["Sam"].update(age=9, interests=["space"])
    updated, _ = kid.get_kid_agent("family", "Sam", surface="voice")
    assert updated is not old
    assert "Age: 9" in updated.system_prompt and "Interests: space" in updated.system_prompt
    assert "Interests: dinosaurs" not in updated.system_prompt
    assert config["content_hash"] == "stored-review-hash"
    assert config["system_prompt"] == "OLD PROFILE"
    assert "practice taking turns" in updated.system_prompt


def test_soul_and_approved_boundaries_refresh_without_stored_hash_change(kid_factory, monkeypatch):
    from app import prompt_synthesis
    kid, config, family = kid_factory
    old, _ = kid.get_kid_agent("family", "Sam")
    monkeypatch.setattr(prompt_synthesis, "_soul_kid_content", "CURRENT SOUL POLICY")
    updated, _ = kid.get_kid_agent("family", "Sam")
    assert updated is not old
    assert updated.system_prompt.startswith("CURRENT SOUL POLICY")
    config["invariants"]["topics_blocked"].append("scary stories")
    changed, _ = kid.get_kid_agent("family", "Sam")
    assert changed is not updated
    assert "scary stories" in sealed(changed.system_prompt)


def test_kid_surface_cache_stays_tenant_scoped_and_invalidatable(kid_factory):
    kid, config, family = kid_factory
    first, _ = kid.get_kid_agent("first", "Sam", surface="voice")
    other, _ = kid.get_kid_agent("second", "Sam", surface="voice")
    assert first is not other
    kid.invalidate_user("first")
    assert kid.get_kid_agent("second", "Sam", surface="voice")[0] is other
    assert kid.get_kid_agent("first", "Sam", surface="voice")[0] is not first


def test_parent_answering_graph_and_token_prompt_share_voice_policy(monkeypatch):
    from app import agent, parent_convai_endpoint
    monkeypatch.setattr(agent, "_agent_cache", AgentCache(4))
    monkeypatch.setattr(agent, "content_catalog_for_prompt", lambda: "LIBRARY CATALOG")
    monkeypatch.setattr(agent, "_dynamic_context", lambda uid: {
        "profile": "CURRENT FAMILY", "household": None, "for_you": None,
    })
    monkeypatch.setattr(agent, "build_parent_tools", lambda uid: ["same approved tools"])
    monkeypatch.setattr(agent, "build_middleware", lambda: ["same middleware"])
    monkeypatch.setattr(agent, "create_agent", lambda **kwargs: SimpleNamespace(**kwargs))
    text = agent.get_agent("parent")
    voice = parent_convai_endpoint.get_agent("parent")
    assert voice.system_prompt.startswith(text.system_prompt)
    assert "## Voice mode" not in text.system_prompt
    assert "## Voice mode" in voice.system_prompt
    assert "mvp://library/{id}" in voice.system_prompt
    assert "Never claim a task succeeded" in voice.system_prompt
    assert voice.tools == text.tools and voice.middleware == text.middleware
    assert voice.checkpointer is text.checkpointer
    assert voice.system_prompt == agent.build_system_prompt_for("parent", surface="voice")
    assert agent.get_agent("parent", surface="voice") is voice
    again = agent.get_agent("parent")
    assert again.system_prompt == text.system_prompt
    agent._agent_cache.pop("parent")
    assert len(agent._agent_cache) == 0


def test_explicit_voice_policy_does_not_mutate_saved_invariants():
    from app.prompt_synthesis import build_system_prompt
    invariant = {"voice_mode": False, "topics_blocked": ["violence"]}
    prompt = build_system_prompt(kid_profile={"name": "Sam", "age": 6}, invariants=invariant, voice_mode=True)
    assert "## Voice mode" in prompt
    assert invariant["voice_mode"] is False
