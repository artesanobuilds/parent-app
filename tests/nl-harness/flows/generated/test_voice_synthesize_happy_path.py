# flows/generated/test_voice_synthesize_happy_path.py
#
# @generated_from: specs/tier-1/voice-synthesize-happy-path.flow.yml
# @generated_at: 2026-06-02T00:00:00Z
# @modules: auth, consent, kid_agent, voice
# @promoted_by: (none -- awaiting review)
#
import os
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = [
    # OBSOLETE: v1 per-fragment voice synthesis (/voice/synthesize + voice_fragment
    # SSE events) was removed in the ElevenLabs ConvAI v2 migration (2026-06). This
    # spec targets a deleted endpoint and can never pass as written — re-author for
    # ConvAI v2 (/voice/convai-token) or delete the spec. NOT a dep-bump regression.
    pytest.mark.skip(reason="v1 /voice/synthesize removed in ConvAI v2 migration; re-author or delete"),
    pytest.mark.tier1,
    pytest.mark.sse,
    pytest.mark.requires_openai,
]


@pytest.mark.asyncio
async def test_voice_synthesize_returns_streamed_mp3_with_sentinel(flow_ctx, kid_agent_parent):
    if not os.environ.get("RUN_ELEVENLABS_FLOWS", "").lower() in ("1", "true", "yes"):
        pytest.skip(
            "RUN_ELEVENLABS_FLOWS not enabled — this spec spends real ElevenLabs "
            "quota. Set RUN_ELEVENLABS_FLOWS=true to opt in."
        )

    kap = kid_agent_parent

    reply_id, fragment_id = await kap.voice_fragment_id_for_last_reply()
    assert reply_id and fragment_id, "persona helper returned empty ids"

    resp = flow_ctx.get(
        f"/voice/synthesize/{reply_id}/{fragment_id}",
        as_=kap.parent,
        params=None,
    )
    # Auth header is set by `as_=`; the kid_pin is a separate custom header
    # that the FlowContext wrapper doesn't model — drop to httpx for this call.
    import httpx
    with httpx.Client(base_url=flow_ctx.base_url, timeout=60.0) as client:
        resp = client.get(
            f"/voice/synthesize/{reply_id}/{fragment_id}",
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("Content-Type", "").startswith("audio/mpeg"), \
        f"expected audio/mpeg, got {resp.headers.get('Content-Type')!r}"
    assert resp.headers.get("X-Voice-Complete") == "1", \
        f"expected X-Voice-Complete: 1, got {resp.headers.get('X-Voice-Complete')!r}"
    assert len(resp.content) >= 256, (
        f"voice body suspiciously small ({len(resp.content)} bytes) — "
        "stream may have aborted before any audio was produced"
    )

    # Idempotent: same id pair returns 200 again
    with httpx.Client(base_url=flow_ctx.base_url, timeout=60.0) as client:
        resp2 = client.get(
            f"/voice/synthesize/{reply_id}/{fragment_id}",
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    assert resp2.status_code == 200, resp2.text
