# flows/generated/test_voice_synthesize_fallback_signaling.py
#
# @generated_from: specs/tier-1/voice-synthesize-fallback-signaling.flow.yml
# @generated_at: 2026-06-02T00:00:00Z
# @modules: auth, voice, telemetry
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
async def test_voice_synthesize_503s_with_key_missing_when_el_unset(
    flow_ctx, kid_agent_parent, admin
):
    """
    With ELEVENLABS_API_KEY unset on the backend, /voice/synthesize must
    return 503 + detail.fallback_reason=key_missing — the structured signal
    iOS uses to switch this agent to AVSpeechSynthesizer for the session.

    Gated on an admin /admin/voice/health probe so we never run this against
    a real EL-enabled box (where it'd flap depending on quota).
    """
    kap = kid_agent_parent

    health = flow_ctx.get("/admin/voice/health", as_=admin)
    if health.status_code == 404:
        pytest.skip(
            "Backend does not expose GET /admin/voice/health — can't tell "
            "whether ELEVENLABS_API_KEY is set; refusing to run blind. Add "
            "the health endpoint alongside the v1 voice impl and re-enable."
        )
    assert health.status_code == 200, health.text
    body = health.json()
    if body.get("elevenlabs_enabled") is True:
        pytest.skip(
            "Backend has ELEVENLABS_API_KEY set — this spec only validates "
            "the key_missing fallback path; run it on a backend with EL "
            "intentionally disabled."
        )

    reply_id, fragment_id = await kap.voice_fragment_id_for_last_reply()

    with httpx.Client(base_url=flow_ctx.base_url, timeout=30.0) as client:
        resp = client.get(
            f"/voice/synthesize/{reply_id}/{fragment_id}",
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    assert resp.status_code == 503, (
        f"EL-unset /voice/synthesize must 503; got {resp.status_code}: "
        f"{resp.text[:200]}"
    )
    assert resp.headers.get("Content-Type", "").startswith("application/json"), (
        f"503 body should be JSON, not audio; got Content-Type="
        f"{resp.headers.get('Content-Type')!r}"
    )
    body = resp.json()
    detail = body.get("detail")
    assert isinstance(detail, dict), f"expected detail dict, got {body!r}"
    assert detail.get("fallback_reason") == "key_missing", (
        f"detail.fallback_reason should be 'key_missing'; got {detail!r}"
    )
