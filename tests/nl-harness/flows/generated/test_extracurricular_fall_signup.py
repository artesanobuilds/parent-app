# flows/generated/test_extracurricular_fall_signup.py
#
# @generated_from: specs/tier-1/extracurricular-fall-signup.flow.yml
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
    parts = []
    for e in stream.events:
        j = e.json
        if isinstance(j, dict) and j.get("type") == "token":
            parts.append(j.get("content", ""))
    return "".join(parts)


def test_weekly_class_signup_lands_on_the_board(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (tracks an activity); skipped on prod")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; /cos/chat would spend tokens")

    parent = existing_parent
    auth = {"Authorization": f"Bearer {parent.token}"}

    s = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={
            "user_id": parent.user_id,
            "thread_id": "extracurricular-flow",
            "message": (
                "TestKid is doing soccer this fall — every Tuesday at 4pm, "
                "$200 for the season. I already signed them up."
            ),
        },
        headers=auth,
    )
    assert s.status_code == 200
    assert _non_empty_reply(s).strip(), "assistant reply was empty"

    acts = flow_ctx.get("/cos/activities", as_=parent, params={"status": "signed_up"})
    assert acts.status_code == 200, acts.text
    body = acts.json()
    assert "activities" in body
    soccer = [a for a in body["activities"] if "soccer" in (a.get("name") or "").lower()]
    assert soccer, f"no signed_up soccer activity found: {body['activities']}"

    # Recurring date model: the rrule is the source of truth; a derived
    # recurring appointment (activity_id back-reference) is equivalent proof.
    a = soccer[0]
    has_rrule = "WEEKLY" in (a.get("rrule") or "").upper()
    recurring = flow_ctx.get("/cos/recurring", as_=parent)
    derived = [
        r for r in (recurring.json().get("recurring") or recurring.json().get("appointments") or [])
        if r.get("activity_id") == a.get("id")
    ] if recurring.status_code == 200 else []
    assert has_rrule or derived, (
        f"activity has neither a weekly rrule nor a derived recurring row: {a}"
    )

    board = flow_ctx.get("/cos/plan/board", as_=parent)
    assert board.status_code == 200, board.text
    stages = board.json()["stages"]
    cards = [c for s_ in stages for c in s_.get("activities", []) if c["id"] == a["id"]]
    assert cards, "tracked activity missing from the board"
    if has_rrule:
        assert (cards[0].get("when") or "").strip(), "board card has no when line"
