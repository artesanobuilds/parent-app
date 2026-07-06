"""
Offline guard for the kid-agent moderation crisis tier (app/moderation.py).

The deterministic regex tier (`scan_for_crisis`) and the streaming gate's
crisis path run with NO network, so we can snapshot their verdicts. This is the
safety-critical behavior that must survive the dependency bump untouched.

The OpenAI moderation API and the age-classifier LLM tiers are intentionally NOT
exercised here (they need the network); they're covered live by
tests/nl-harness/kid-agent-lifecycle.flow.yml.
"""
from __future__ import annotations

import pytest

from app.moderation import (
    ModerationResult,
    StreamingModerator,
    StreamingState,
    moderate_input,
    scan_for_crisis,
    scan_for_crisis_detailed,
    unfreeze_all,
)

# Phrases that MUST trip the crisis regex, with expected (category, severity).
CRISIS_CASES = [
    ("I want to kill myself", "suicide_direct", "high"),
    ("sometimes I want to hurt myself", "self_harm", "high"),
    ("tonight I'll end it", "suicide_direct", "imminent"),
    ("I've been cutting my wrist", "self_harm", "high"),
    ("my dad hits me when he's mad", "abuse", "high"),
    ("my uncle hit me", "abuse", "high"),  # past tense still fires (requires "me")
    ("can you send me nudes", "grooming", "imminent"),
    ("I haven't eaten in three days", "ed", "high"),
    ("quiero morirme", "suicide_direct", "high"),  # Spanish coverage
]

# Ordinary distress that must NOT be treated as a crisis (false positives are
# cold and dismissive — the taxonomy comment in moderation.py calls this out).
BENIGN_CASES = [
    "I had a fight with my friend and I'm sad",
    "I'm scared after watching a movie",
    "My goldfish died and I miss him",
    "I don't want to go to school today",
    "I'm so hungry, I haven't eaten since breakfast",
    "we lost the soccer game and I'm frustrated",
    # "[pronoun] hit [not-me]" must NOT fire — this benign phrase locked a real
    # companion before the abuse regex required a "…me" object.
    "Oh, she hit a guardrail",
    "he hit the ball really far at practice",
    "my brother hit a home run",
]


@pytest.mark.parametrize("text,category,severity", CRISIS_CASES)
def test_crisis_phrases_match(text, category, severity):
    cp = scan_for_crisis_detailed(text)
    assert cp is not None, f"expected a crisis match for: {text!r}"
    assert cp.category == category, f"{text!r}: category {cp.category!r} != {category!r}"
    assert cp.severity == severity, f"{text!r}: severity {cp.severity!r} != {severity!r}"


@pytest.mark.parametrize("text", BENIGN_CASES)
def test_benign_phrases_do_not_match(text):
    assert scan_for_crisis(text) is None, f"false-positive crisis match for: {text!r}"


def test_moderate_input_short_circuits_on_crisis_without_network():
    """The crisis branch returns before any OpenAI call, so this is offline."""
    unfreeze_all()  # ensure no leftover global freeze from another test
    result = moderate_input(
        user_id="u1", kid_name="Ceiba", agent_id="agent-1",
        age_band="middle", text="I want to kill myself",
    )
    assert isinstance(result, ModerationResult)
    assert result.flagged is True
    assert result.severity == "crisis"
    assert result.suggested_action == "crisis_route"


def test_streaming_moderator_blocks_on_emergent_crisis():
    """A crisis phrase appearing in the output stream flips the gate to BLOCKED."""
    sm = StreamingModerator(
        user_id="u1", kid_name="Ceiba", agent_id="agent-1", age_band="middle",
    )
    # With KID_OUTPUT_BUFFER_CHARS=0 (default) the gate starts in STREAMING and
    # the per-token crisis regex is the active guard.
    benign = sm.feed("Let's talk about dinosaurs! ")
    assert benign == ["Let's talk about dinosaurs! "]
    assert sm.state == StreamingState.STREAMING

    emitted = sm.feed("actually I want to kill myself")
    assert emitted == [], "no further tokens may be emitted once crisis is detected"
    assert sm.state == StreamingState.BLOCKED
    assert sm.block_reason is not None and sm.block_reason.severity == "crisis"
    assert "grown-up needs to know" in sm.replacement_message()
