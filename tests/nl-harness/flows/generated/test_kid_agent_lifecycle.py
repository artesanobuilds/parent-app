# flows/generated/test_kid_agent_lifecycle.py
#
# @generated_from: specs/tier-1/kid-agent-lifecycle.flow.yml
# @generated_at: 2026-05-31T15:00:00Z
# @modules: auth, consent, profile, kid_agent, moderation, audit
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

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


# A crisis input the moderation gate should catch. Kept generic — the
# patterns in app/moderation.py cover self-harm, suicide, abuse, etc. We
# pick a phrasing unambiguous enough to fire any reasonable classifier.
CRISIS_INPUT = "i want to hurt myself tonight"


def test_kid_agent_full_lifecycle_with_crisis_lock_and_revive(flow_ctx, kid_agent_parent):
    kap = kid_agent_parent  # parent + introduced kid agent + PIN set
    parent = kap.parent
    agent_id = kap.agent_id
    assert agent_id, "kid_agent_parent fixture did not return an agent_id"

    # ── Step 1: normal kid-chat round-trip ──────────────────────────
    normal_stream = post_sse(
        flow_ctx.base_url,
        "/kid-chat",
        json_body={
            "user_id": parent.user_id,
            "kid_name": kap.kid_name,
            "kid_pin": kap.kid_pin,
            "thread_id": "nl-harness-thread-1",
            "message": "Hi! What's your favorite color?",
        },
        headers={"Authorization": f"Bearer {parent.token}"},
        timeout=60,
    )
    assert normal_stream.status_code == 200
    assert normal_stream.events, "kid-chat returned no SSE events for a normal message"

    # ── Step 2: crisis input → moderation gate fires + lock lands ───
    crisis_stream = post_sse(
        flow_ctx.base_url,
        "/kid-chat",
        json_body={
            "user_id": parent.user_id,
            "kid_name": kap.kid_name,
            "kid_pin": kap.kid_pin,
            "thread_id": "nl-harness-thread-1",
            "message": CRISIS_INPUT,
        },
        headers={"Authorization": f"Bearer {parent.token}"},
        timeout=60,
    )
    assert crisis_stream.status_code == 200
    crisis_text = crisis_stream.text() + " ".join(
        e.event for e in crisis_stream.events
    )
    # The replacement message or `crisis_locked` event signals the gate fired.
    # We don't pin the exact wording — what matters is the side-effect (the
    # lock row) verified next.

    # ── Step 3: GET /kid-agent/crisis-locks shows the lock ──────────
    def lock_present() -> bool:
        resp = flow_ctx.get(
            "/kid-agent/crisis-locks",
            params={"user_id": parent.user_id},
            as_=parent,
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

    # ── Step 4: parent revives the agent ────────────────────────────
    revive_resp = flow_ctx.post(f"/kid-agent/{agent_id}/revive", as_=parent)
    assert revive_resp.status_code == 200, revive_resp.text
    revive_body = revive_resp.json()
    assert revive_body.get("ok") is True, f"revive returned {revive_body!r}"
    assert revive_body.get("agent_id") == agent_id
    assert revive_body.get("kid_name") == kap.kid_name

    # ── Step 5: lock is gone after revive ───────────────────────────
    locks_after = flow_ctx.get(
        "/kid-agent/crisis-locks",
        params={"user_id": parent.user_id},
        as_=parent,
    ).json().get("locks") or []
    for lock in locks_after:
        assert lock.get("agent_id") != agent_id, \
            f"agent {agent_id} still locked after revive: {lock}"

    # ── Step 6: moderation events recorded the crisis ───────────────
    mod_resp = flow_ctx.get(
        "/kid-moderation/events",
        params={"user_id": parent.user_id, "kid_name": kap.kid_name},
        as_=parent,
    )
    assert mod_resp.status_code == 200
    events = mod_resp.json().get("events") or []
    assert len(events) >= 1, (
        "kid-moderation/events returned no events despite a crisis input "
        f"({CRISIS_INPUT!r}). Sliding-window gate may be regressing."
    )
