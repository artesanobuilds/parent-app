"""
Golden / contract tests for kid-agent prompt synthesis (app/prompt_synthesis.py).

Stage 2 (`build_system_prompt`, `compute_content_hash`) is pure Python and
deterministic — no LLM — so these are true golden tests. Stage 1 (`synthesize`)
is exercised with the LLM call monkeypatched out, so we assert the SynthesisResult
contract without touching the network.

This is the highest-value offline guard for the dep bump: if a langchain/pydantic
version change alters how `SynthesizedInvariants` serializes or how the sealed
prompt is assembled, the content_hash (cache key) or the safety block would drift
and these tests break.
"""
from __future__ import annotations

import re

import app.prompt_synthesis as ps
from app.prompt_synthesis import (
    SYNTHESIS_VERSION,
    SynthesisResult,
    _soul_kid_content,
    build_system_prompt,
    compute_content_hash,
    synthesize,
)

# A representative invariants dict (the shape Stage 1 produces / stores).
_INVARIANTS = {
    "agent_display_name": "Nova",
    "personality_description": "You are warm but not soft. You ask more than you answer.",
    "interests_summary": "Loves dinosaurs and is working on reading.",
    "topics_allowed": ["dinosaurs", "space"],
    "topics_blocked": ["violence", "death"],
    "tools_enabled": {"web_search": False},
    "goals": ["build reading confidence"],
    "persona_examples": ["Ooh, tell me more!", "Hmm, let's figure it out together."],
    "voice_mode": False,
}

_KID = {"name": "Ceiba", "age": 8, "interests": ["dinosaurs", "drawing"]}


def test_build_system_prompt_is_deterministic_and_sealed():
    a = build_system_prompt(kid_profile=_KID, invariants=_INVARIANTS)
    b = build_system_prompt(kid_profile=_KID, invariants=_INVARIANTS)
    assert a == b, "Stage 2 must be a pure function (same inputs -> same output)"

    # The sealed safety block and the parent-set slots must be present.
    assert "<non_negotiable>" in a and "</non_negotiable>" in a
    assert "Nova" in a  # display name
    assert "Ceiba" in a  # kid name woven in
    assert "- violence" in a and "- death" in a  # blocked clusters rendered
    assert _soul_kid_content[:40] in a  # soul_kid.md is prepended


def test_voice_mode_appends_tts_guidance():
    voiced = dict(_INVARIANTS, voice_mode=True)
    out = build_system_prompt(kid_profile=_KID, invariants=voiced)
    assert "## Voice mode" in out
    assert "spoken aloud" in out
    # And the non-voice variant must NOT contain it.
    assert "## Voice mode" not in build_system_prompt(kid_profile=_KID, invariants=_INVARIANTS)


def test_content_hash_is_16_char_hex_and_idempotent():
    h1 = compute_content_hash(
        kid_profile=_KID, invariants=_INVARIANTS,
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    h2 = compute_content_hash(
        kid_profile=_KID, invariants=_INVARIANTS,
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    assert h1 == h2
    # NOTE: implementation truncates sha256 to 16 hex chars (`[:16]`).
    assert re.fullmatch(r"[0-9a-f]{16}", h1), f"expected 16-char hex, got {h1!r}"


def test_content_hash_changes_when_invariants_change():
    base = compute_content_hash(
        kid_profile=_KID, invariants=_INVARIANTS,
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    changed = compute_content_hash(
        kid_profile=_KID,
        invariants=dict(_INVARIANTS, topics_blocked=["violence", "death", "guns"]),
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    assert base != changed, "a change to the safety invariants must bust the cache key"


def test_content_hash_stable_under_dict_key_reordering():
    reordered = {k: _INVARIANTS[k] for k in reversed(list(_INVARIANTS.keys()))}
    a = compute_content_hash(
        kid_profile=_KID, invariants=_INVARIANTS,
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    b = compute_content_hash(
        kid_profile=_KID, invariants=reordered,
        soul_kid=_soul_kid_content, synthesis_version=SYNTHESIS_VERSION,
    )
    assert a == b, "hash uses sort_keys=True; key order must not matter"


def test_synthesize_contract_with_llm_mocked(monkeypatch):
    """`synthesize()` must return a well-formed SynthesisResult without calling the LLM."""
    monkeypatch.setattr(ps, "_llm_extract_invariants", lambda **kw: dict(_INVARIANTS))

    result = synthesize(brief="make it about dinosaurs", kid_profile=_KID)

    assert isinstance(result, SynthesisResult)
    assert isinstance(result.system_prompt, str) and result.system_prompt.strip()
    assert result.invariants == _INVARIANTS
    assert re.fullmatch(r"[0-9a-f]{16}", result.content_hash)
    assert result.model == ps.SYNTHESIS_MODEL
    assert isinstance(result.summary, str) and result.summary.strip()
    # The synthesized prompt must equal a direct Stage-2 build of the same slots.
    assert result.system_prompt == build_system_prompt(kid_profile=_KID, invariants=_INVARIANTS)
