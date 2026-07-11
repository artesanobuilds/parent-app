# flows/generated/test_cos_chat_power_tools.py
#
# @generated_from: specs/tier-1/cos-chat-power-tools.flow.yml
# @generated_at: 2026-07-10T00:00:00Z
# @modules: cos, chat, profile, research
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

pytestmark = [pytest.mark.tier1, pytest.mark.sse, pytest.mark.requires_openai]


def _non_empty_reply(stream) -> str:
    """Concatenate the streamed `token` frames into the assistant's reply."""
    parts = []
    for e in stream.events:
        j = e.json
        if isinstance(j, dict) and j.get("type") == "token":
            parts.append(j.get("content", ""))
    return "".join(parts)


def test_cos_chat_power_tools(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (tracks activities, enqueues research); skipped on prod")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; /cos/chat + web lookup would spend tokens")

    parent = existing_parent
    auth = {"Authorization": f"Bearer {parent.token}"}
    thread = {"user_id": parent.user_id, "thread_id": "power-tools-flow"}

    # ── Precondition: profile has a ZIP so StartDiscovery has a location ─
    # (The existing-parent preset seeds no postal_code; the spec requires one.)
    seed = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent.display_name,
            "postal_code": "95448",
            "kids": [
                {"name": "TestKid", "age": "7", "grade_band": "elementary"},
            ],
        },
        as_=parent,
    )
    assert seed.status_code == 200, seed.text

    # ── Turn 1: "what can you do?" → Help tool relayed warmly ────────────
    s1 = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={**thread, "message": "what can you actually do for me?"},
        headers=auth,
    )
    assert s1.status_code == 200
    reply1 = _non_empty_reply(s1)
    assert reply1.strip(), "turn-1 assistant reply was empty"
    # "Names several capabilities": the Help text is capability-dense; a warm
    # relay should surface at least two of these capability words.
    capability_words = [
        "camp", "activit", "calendar", "to-do", "todo", "coverage",
        "discover", "track", "decide", "email", "week",
    ]
    hits = [w for w in capability_words if w in reply1.lower()]
    assert len(hits) >= 2, f"reply names too few capabilities ({hits}): {reply1[:300]}"

    # ── Turn 2: "I signed up for Camp Galileo" → LookupAndSaveActivity ──
    s2 = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={**thread, "message": "I signed up for Camp Galileo last night on their site."},
        headers=auth,
    )
    assert s2.status_code == 200
    assert _non_empty_reply(s2).strip(), "turn-2 assistant reply was empty"

    # After the save turn, the activity exists as signed_up via the normal API.
    acts = flow_ctx.get("/cos/activities", as_=parent, params={"status": "signed_up"})
    assert acts.status_code == 200, acts.text
    body = acts.json()
    assert "activities" in body
    names = [(a.get("name") or "").lower() for a in body["activities"]]
    assert any("galileo" in n for n in names), (
        f"expected a signed_up activity referencing Camp Galileo, got {names}"
    )

    # ── Turn 3: "go find art camps near us" → StartDiscovery enqueues ───
    runs_before = flow_ctx.get("/research/runs", as_=parent)
    assert runs_before.status_code == 200, runs_before.text
    ids_before = {r.get("id") for r in runs_before.json().get("runs", [])}

    s3 = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={**thread, "message": "go find art camps near us"},
        headers=auth,
    )
    assert s3.status_code == 200
    assert _non_empty_reply(s3).strip(), "turn-3 assistant reply was empty"

    def _new_run_ids():
        resp = flow_ctx.get("/research/runs", as_=parent)
        if resp.status_code != 200:
            return set()
        return {r.get("id") for r in resp.json().get("runs", [])} - ids_before

    flow_ctx.wait_for(
        lambda: bool(_new_run_ids()),
        timeout_s=15,
        description="StartDiscovery enqueued a research run",
    )

    # Cancel whatever StartDiscovery enqueued so no orphan work is left.
    for run_id in _new_run_ids():
        flow_ctx.register_cleanup(
            f"cancel research run {run_id}",
            lambda rid=run_id: flow_ctx.post(f"/research/runs/{rid}/cancel", json={}, as_=parent),
        )
