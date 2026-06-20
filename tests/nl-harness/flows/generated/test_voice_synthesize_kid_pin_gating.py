# flows/generated/test_voice_synthesize_kid_pin_gating.py
#
# @generated_from: specs/tier-1/voice-synthesize-kid-pin-gating.flow.yml
# @generated_at: 2026-06-02T00:00:00Z
# @modules: auth, kid_agent, voice
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import httpx
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
async def test_voice_synthesize_rejects_missing_or_wrong_kid_pin(flow_ctx, kid_agent_parent):
    kap = kid_agent_parent
    reply_id, fragment_id = await kap.voice_fragment_id_for_last_reply()

    url = f"/voice/synthesize/{reply_id}/{fragment_id}"
    with httpx.Client(base_url=flow_ctx.base_url, timeout=30.0) as client:
        # No bearer token: 401
        resp = client.get(url)
        assert resp.status_code == 401, (
            f"anon /voice/synthesize should 401; got {resp.status_code}: {resp.text[:200]}"
        )

        # Bearer token but no X-Kid-Pin header: 401 (PIN check is default-closed)
        resp = client.get(url, headers={"Authorization": f"Bearer {kap.token}"})
        assert resp.status_code == 401, (
            f"missing kid_pin should 401; got {resp.status_code}: {resp.text[:200]}"
        )

        # Bearer token + wrong X-Kid-Pin: 401
        resp = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": "0000-not-the-real-pin",
            },
        )
        assert resp.status_code == 401, (
            f"wrong kid_pin should 401; got {resp.status_code}: {resp.text[:200]}"
        )

        # Correct token + correct kid_pin: reaches the provider. Accept 200
        # (EL configured) OR 503 with fallback_reason (EL unconfigured) —
        # what we're proving here is the gate doesn't reject the right pair.
        resp = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
        assert resp.status_code not in (401, 403), (
            f"correct auth should NOT 401/403; got {resp.status_code}: {resp.text[:200]}"
        )
        assert resp.status_code in (200, 429, 503), (
            f"correct auth landed at unexpected status {resp.status_code}: {resp.text[:200]}"
        )
