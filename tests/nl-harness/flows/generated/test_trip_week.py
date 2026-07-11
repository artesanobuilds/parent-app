# flows/generated/test_trip_week.py
#
# @generated_from: specs/tier-1/trip-week.flow.yml
# @generated_at: 2026-07-11T00:00:00Z
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


def test_booked_trip_lands_with_range_and_prep_todos(flow_ctx, existing_parent):
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
            "thread_id": "trip-week-flow",
            "message": (
                "We're taking the kids to Lake Tahoe June 14 through 18 next "
                "summer — it's already booked. Get it on the plan."
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
    trips = [a for a in body["activities"] if "tahoe" in (a.get("name") or "").lower()]
    assert trips, f"no signed_up Tahoe activity found: {body['activities']}"
    a = trips[0]
    assert a.get("activity_type") == "trip", f"expected activity_type=trip: {a}"

    # date_range model: the REAL start and end, never a fabricated week.
    start = str(a.get("start_date") or "")[:10]
    end = str(a.get("end_date") or "")[:10]
    assert start and end and start != end, (
        f"trip must carry a real range (start != end): start={start!r} end={end!r}"
    )

    board = flow_ctx.get("/cos/plan/board", as_=parent)
    assert board.status_code == 200, board.text
    stages = board.json()["stages"]
    cards = [c for s_ in stages for c in s_.get("activities", []) if c["id"] == a["id"]]
    assert cards, "tracked trip missing from the board"
    when = (cards[0].get("when") or "").strip()
    assert when and "–" in when, f"board card should render the range: when={when!r}"

    # Enter-WATCHED prep extras: at least the packing to-do exists.
    todos = flow_ctx.get("/cos/todos", as_=parent)
    assert todos.status_code == 200, todos.text
    todo_list = todos.json().get("todos") or []
    packing = [
        t for t in todo_list
        if t.get("activity_id") == a["id"] and "packing" in (t.get("title") or "").lower()
    ]
    assert packing, f"no packing to-do seeded for the trip: {todo_list}"
