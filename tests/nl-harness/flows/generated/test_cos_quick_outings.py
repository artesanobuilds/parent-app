# flows/generated/test_cos_quick_outings.py
#
# @generated_from: specs/tier-1/cos-quick-outings.flow.yml
# @generated_at: 2026-07-10T00:00:00Z
# @modules: cos, chat, profile
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


def test_quick_weekend_outings_are_ephemeral(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (re-seeds profile); skipped on the read-only env")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; /cos/chat + web search would spend tokens")

    parent = existing_parent
    auth = {"Authorization": f"Bearer {parent.token}"}

    # ── Re-seed the profile with two very young kids (toddler + infant) ──
    seed = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent.display_name,
            "kids": [
                {"name": "Nova", "age": "2.5", "grade_band": "preschool"},
                {"name": "Baby", "age": "0.4"},
            ],
        },
        as_=parent,
    )
    assert seed.status_code == 200, seed.text

    # ── Clean slate: no tracked activities before we start ──────────────
    acts_before = flow_ctx.get("/cos/activities", as_=parent)
    assert acts_before.status_code == 200, acts_before.text
    assert "activities" in acts_before.json()
    assert acts_before.json()["activities"] == [], "expected a clean activity list"

    thread = {"user_id": parent.user_id, "thread_id": "outings-flow"}

    # ── Turn 1: the outing ask (agent should offer to size the list) ────
    s1 = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={**thread, "message": "what can we do with the kids in San Francisco this weekend?"},
        headers=auth,
    )
    assert s1.status_code == 200
    assert _non_empty_reply(s1).strip(), "turn-1 assistant reply was empty"

    # ── Turn 2: answer how many ─────────────────────────────────────────
    s2 = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={**thread, "message": "three please"},
        headers=auth,
    )
    assert s2.status_code == 200
    assert _non_empty_reply(s2).strip(), "turn-2 assistant reply was empty"

    # ── Ephemerality: NOTHING was saved to the plan ─────────────────────
    acts_after = flow_ctx.get("/cos/activities", as_=parent)
    assert acts_after.status_code == 200, acts_after.text
    assert acts_after.json()["activities"] == [], \
        "outing suggestions must be ephemeral — no tracked activity should be created"

    board = flow_ctx.get("/cos/plan/board", as_=parent)
    assert board.status_code == 200, board.text
    body = board.json()
    assert "stages" in body
    non_empty = [s for s in body["stages"] if s.get("activities")]
    assert non_empty == [], f"nothing should be on the board, found: {non_empty}"
