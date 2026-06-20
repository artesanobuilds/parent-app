# flows/generated/test_voice_synthesize_crisis_lock.py
#
# @generated_from: specs/tier-1/voice-synthesize-crisis-lock.flow.yml
# @generated_at: 2026-06-02T00:00:00Z
# @modules: auth, kid_agent, moderation, voice
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import httpx
import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.sse import post_sse  # noqa: E402

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


CRISIS_INPUT = "i want to hurt myself tonight"


@pytest.mark.asyncio
async def test_voice_synthesize_403s_after_crisis_lock(flow_ctx, kid_agent_parent):
    kap = kid_agent_parent
    agent_id = kap.agent_id
    assert agent_id, "kid_agent_parent fixture did not return an agent_id"

    # ── Step 1: clean reply, capture a (reply_id, fragment_id) pre-lock ──
    reply_id, fragment_id = await kap.voice_fragment_id_for_last_reply()
    url = f"/voice/synthesize/{reply_id}/{fragment_id}"

    # Sanity: the pair is voiceable before the lock lands (skipping if EL
    # isn't configured — the lock-not-bypass behavior is what we care about).
    with httpx.Client(base_url=flow_ctx.base_url, timeout=60.0) as client:
        pre = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    if pre.status_code not in (200, 503):
        pytest.fail(
            f"pre-crisis /voice/synthesize landed at unexpected status "
            f"{pre.status_code}: {pre.text[:200]}"
        )

    # ── Step 2: feed a crisis input → lock lands ─────────────────────────
    crisis_stream = post_sse(
        flow_ctx.base_url,
        "/kid-chat",
        json_body={
            "user_id": kap.user_id,
            "kid_name": kap.kid_name,
            "kid_pin": kap.kid_pin,
            "thread_id": "voice-crisis-thread",
            "message": CRISIS_INPUT,
        },
        headers={"Authorization": f"Bearer {kap.token}"},
        timeout=60,
    )
    assert crisis_stream.status_code == 200

    def lock_present() -> bool:
        resp = flow_ctx.get(
            "/kid-agent/crisis-locks",
            params={"user_id": kap.user_id},
            as_=kap.parent,
        )
        if resp.status_code != 200:
            return False
        return any(
            lock.get("agent_id") == agent_id
            for lock in (resp.json().get("locks") or [])
        )

    flow_ctx.wait_for(
        lock_present,
        timeout_s=10.0,
        interval_s=0.5,
        description=f"crisis lock for agent_id={agent_id}",
    )

    # ── Step 3: same fragment now 403s ───────────────────────────────────
    with httpx.Client(base_url=flow_ctx.base_url, timeout=30.0) as client:
        locked = client.get(
            url,
            headers={
                "Authorization": f"Bearer {kap.token}",
                "X-Kid-Pin": kap.kid_pin,
            },
        )
    assert locked.status_code == 403, (
        f"locked agent /voice/synthesize must 403; got {locked.status_code}: "
        f"{locked.text[:200]}. Crisis lock not being honored on the voice path?"
    )
