# flows/generated/test_voice_convai_parent_cards.py
#
# @generated_from: specs/tier-1/voice-convai-parent-cards.flow.yml
# @generated_at: 2026-07-23T00:00:00Z
# @modules: auth, chat, content, voice
# @promoted_by: (none -- awaiting review)
#
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

# Make `lib` importable even when pytest is invoked from a different cwd.
HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.sse import post_sse  # noqa: E402

pytestmark = [
    pytest.mark.tier1,
    pytest.mark.sse,
    pytest.mark.requires_openai,
]

CONVAI_PATH = "/v1/parent/chat/completions"
CARD_TOOLS = ("show_article", "show_community_post")

# Phrased to invite a content link without demanding one — the coach may or may
# not cite. Both outcomes are valid; what must hold either way is that no URL is
# ever spoken and any card tool that fires is well-formed.
ASK_FOR_CONTENT = (
    "Bedtime with my 7-year-old is a nightly fight. "
    "Is there something in the library I could read about it?"
)


@pytest.fixture
def convai_secret() -> str:
    """Self-skip when the shared secret isn't in the harness process — without
    it every request is a correct 401 and the flow asserts nothing.

    A FIXTURE, listed first in the test signature, so the skip lands before the
    persona is seeded and before the live turn spends model tokens.
    """
    secret = os.environ.get("ELEVENLABS_CONVAI_SECRET", "").strip()
    if not secret:
        pytest.skip(
            "ELEVENLABS_CONVAI_SECRET not exported to the harness — the ConvAI "
            "Custom-LLM endpoints can only be exercised with the backend's "
            "shared secret."
        )
    return secret


def _convai_body(message: str, extra: dict | None) -> dict:
    body: dict = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": message}],
        "stream": True,
    }
    if extra is not None:
        body["elevenlabs_extra_body"] = extra
    return body


def _frames(stream) -> list:
    return [e.json for e in stream.events]


def _content_frames(stream) -> list:
    return [
        f for f in _frames(stream)
        if isinstance(f, dict) and "content" in f["choices"][0]["delta"]
    ]


def _spoken(stream) -> str:
    return "".join(f["choices"][0]["delta"]["content"] for f in _content_frames(stream))


def _tool_frames(stream) -> list:
    return [
        f for f in _frames(stream)
        if isinstance(f, dict) and "tool_calls" in f["choices"][0]["delta"]
    ]


def _assert_openai_sse_shape(stream) -> None:
    frames = _frames(stream)
    assert frames, "ConvAI endpoint returned an empty SSE stream"
    assert frames[-1] == "[DONE]", f"stream did not terminate with [DONE]: {frames[-1]!r}"
    for frame in frames[:-1]:
        assert isinstance(frame, dict), f"non-JSON SSE frame: {frame!r}"
        assert frame["object"] == "chat.completion.chunk", \
            f"ElevenLabs only parses chat.completion.chunk, got {frame['object']!r}"
        assert frame["choices"][0]["index"] == 0


def test_parent_voice_probe_auth_and_card_tools(convai_secret, flow_ctx, existing_parent):
    secret = convai_secret
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS is false; a live parent coaching turn spends tokens")

    parent = existing_parent
    bearer = {"Authorization": f"Bearer {secret}"}

    # ── Step 1: the ElevenLabs console connection probe ─────────────
    probe = post_sse(
        flow_ctx.base_url, CONVAI_PATH,
        json_body=_convai_body("Hello", None),
        headers=bearer, timeout=30,
    )
    assert probe.status_code == 200
    _assert_openai_sse_shape(probe)
    assert _spoken(probe) == "OK", f"probe stub regressed: {_spoken(probe)!r}"

    # The legacy header must authenticate identically — the two console
    # configuration paths send different ones, and dropping either kills a
    # surface silently.
    legacy_probe = post_sse(
        flow_ctx.base_url, CONVAI_PATH,
        json_body=_convai_body("Hello", None),
        headers={"X-ElevenLabs-Secret": secret}, timeout=30,
    )
    assert _spoken(legacy_probe) == "OK"

    with httpx.Client(base_url=flow_ctx.base_url, timeout=30.0) as raw:
        # ── Step 2: auth ────────────────────────────────────────────
        assert raw.post(CONVAI_PATH, json=_convai_body("Hi", None)).status_code == 401
        assert raw.post(
            CONVAI_PATH, json=_convai_body("Hi", None),
            headers={"Authorization": "Bearer definitely-not-the-secret"},
        ).status_code == 401

        # ── Step 3: extra_body without user_id is a 400 ─────────────
        # (kid_name is NOT required here — the parent agent has no kid in the
        # loop. That asymmetry with /v1/chat/completions is deliberate.)
        bad = raw.post(
            CONVAI_PATH,
            json=_convai_body("Hi", {"kid_name": "TestKid", "thread_id": "t"}),
            headers=bearer,
        )
        assert bad.status_code == 400, bad.text

    # ── Step 4: a live coaching turn ────────────────────────────────
    turn = post_sse(
        flow_ctx.base_url, CONVAI_PATH,
        json_body=_convai_body(
            ASK_FOR_CONTENT,
            {"user_id": parent.user_id, "thread_id": "nl-harness-parent-voice"},
        ),
        headers=bearer, timeout=120,
    )
    assert turn.status_code == 200
    _assert_openai_sse_shape(turn)

    spoken = _spoken(turn)
    assert spoken.strip(), "the coach streamed no spoken text at all"

    # THE invariant this endpoint exists for: a URL must never reach TTS.
    assert "mvp://" not in spoken, (
        f"a card URL leaked into spoken text and would be read aloud: {spoken!r}"
    )

    # ── Step 5: any card tool that fired is well-formed ─────────────
    # Whether the coach cites is model-dependent; the SHAPE is not.
    for frame in _tool_frames(turn):
        assert frame["choices"][0]["finish_reason"] is None, (
            "a card tool is display-only — a terminal finish_reason cuts the "
            "coach off mid-sentence."
        )
        for call in frame["choices"][0]["delta"]["tool_calls"]:
            assert call["type"] == "function"
            name = call["function"]["name"]
            assert name in CARD_TOOLS, f"unexpected client tool {name!r}"
            args = json.loads(call["function"]["arguments"])
            assert args.get("id"), f"{name} fired with no content id: {args!r}"
