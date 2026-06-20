# flows/generated/test_voice_synthesize_daily_cap.py
#
# @generated_from: specs/tier-1/voice-synthesize-daily-cap.flow.yml
# @generated_at: 2026-06-02T00:00:00Z
# @modules: auth, voice, cost_controls
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
    pytest.mark.requires_admin_token,
]


@pytest.mark.asyncio
async def test_voice_synthesize_429s_when_daily_cap_exceeded(flow_ctx, kid_agent_parent, admin):
    """
    The cost-containment gate: once tts_usage_daily for a user exceeds the
    per-user cap, /voice/synthesize must 429 with fallback_reason=quota
    BEFORE any ElevenLabs spend. We seed the counter via the admin helper
    rather than burning 50k real chars.
    """
    kap = kid_agent_parent

    reply_id, fragment_id = await kap.voice_fragment_id_for_last_reply()
    url = f"/voice/synthesize/{reply_id}/{fragment_id}"

    # Prove the user can synth today before the bump (skip cleanly if EL
    # isn't configured — daily-cap is the gate under test, not provider).
    with httpx.Client(base_url=flow_ctx.base_url, timeout=60.0) as client:
        pre = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    if pre.status_code == 503:
        pytest.skip(
            "Backend returned 503 fallback before the cap bump — "
            "ELEVENLABS_API_KEY missing on the server; can't isolate the "
            "daily-cap behavior. Configure EL on the backend to run this spec."
        )
    assert pre.status_code in (200, 429), (
        f"pre-bump synth returned unexpected status {pre.status_code}: {pre.text[:200]}"
    )

    # Seed tts_usage_daily near the cap via admin helper. If the helper
    # endpoint isn't present, skip cleanly — the implementer will land it
    # alongside the v1 voice work.
    bump = flow_ctx.post(
        "/admin/voice/usage-bump",
        json={"user_id": kap.user_id, "chars": 10_000_000},  # far above any sane cap
        as_=admin,
    )
    if bump.status_code == 404:
        pytest.skip(
            "Backend does not expose POST /admin/voice/usage-bump yet — "
            "this spec needs the admin helper to seed tts_usage_daily so it "
            "doesn't burn through real ElevenLabs spend. Add the helper "
            "alongside the v1 voice impl and re-enable."
        )
    assert bump.status_code == 200, (
        f"/admin/voice/usage-bump should succeed for an admin token; got "
        f"{bump.status_code}: {bump.text[:200]}"
    )

    # After bump: 429 + fallback_reason=quota
    with httpx.Client(base_url=flow_ctx.base_url, timeout=30.0) as client:
        capped = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    assert capped.status_code == 429, (
        f"over-cap /voice/synthesize must 429; got {capped.status_code}: "
        f"{capped.text[:200]}. Cost containment regression?"
    )
    body = capped.json()
    detail = body.get("detail")
    assert isinstance(detail, dict), f"expected detail dict, got {body!r}"
    assert detail.get("fallback_reason") == "quota", (
        f"detail.fallback_reason should be 'quota'; got {detail!r}"
    )
    assert detail.get("scope") == "user", (
        f"detail.scope should be 'user' for a per-user cap hit; got {detail!r}"
    )
