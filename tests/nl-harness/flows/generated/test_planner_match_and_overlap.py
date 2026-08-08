# flows/generated/test_planner_match_and_overlap.py
#
# @generated_from: specs/tier-1/planner-match-and-overlap.flow.yml
# @generated_at: 2026-08-07T19:10:00Z
# @modules: cos, planning, lifecycle, auth
# @promoted_by: (none -- awaiting review)
#
# Guards the sprint-2 planner wire shape end to end over HTTP. The hermetic
# equivalent is mvp-backend/tests/test_planner_sprint2.py; this one proves the
# same keys survive the actual JSON round trip, which is where the backend and
# iOS drifted the first time.
#
import pytest

pytestmark = pytest.mark.tier1


def _track(flow_ctx, parent, **fields):
    payload = {"user_id": parent.user_id}
    payload.update(fields)
    resp = flow_ctx.post("/cos/activities/track", json=payload, as_=parent)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _card(board, activity_id):
    for stage in board["stages"]:
        for entry in stage["activities"]:
            if entry["id"] == activity_id:
                return entry
    return None


def test_board_requires_auth_and_starts_empty(flow_ctx, new_parent):
    assert flow_ctx.get("/cos/plan/board").status_code == 401
    assert flow_ctx.get("/cos/activities").status_code == 401

    board = flow_ctx.get("/cos/plan/board", as_=new_parent)
    assert board.status_code == 200, board.text
    stages = board.json()["stages"]
    assert all(s["activities"] == [] for s in stages), "a fresh plan is not empty"


def test_match_score_and_reason_reach_the_board(flow_ctx, new_parent):
    """fit_score used to exist only on activity_candidates and was dropped the
    moment a candidate was tracked — so the design's "75% Match" badge had
    nothing to read. v22 carries both fields onto the tracked row."""
    parent = new_parent
    activity_id = _track(
        flow_ctx, parent,
        name="Tom Taylor YMCA Summer Day Camp",
        kid_name="Lily",
        activity_type="camp",
        start_date="2026-06-22",
        end_date="2026-08-28",
        status="signed_up",
        fit_score=0.75,
        fit_reason="Weekly drop-in fits your flexible-weeks preference and Lily's age band.",
        decision_rationale="We picked it because it's closest to home.",
    )

    listed = flow_ctx.get("/cos/activities", as_=parent)
    assert listed.status_code == 200, listed.text
    row = next(a for a in listed.json()["activities"] if a["id"] == activity_id)
    assert row["fit_score"] == 0.75
    assert "flexible-weeks" in row["fit_reason"]
    # The two rationale fields are distinct authors and must not bleed together.
    assert row["decision_rationale"] == "We picked it because it's closest to home."
    assert row["fit_reason"] != row["decision_rationale"]

    card = _card(flow_ctx.get("/cos/plan/board", as_=parent).json(), activity_id)
    assert card is not None, "the tracked activity is missing from every board stage"
    assert card["fit_score"] == 0.75
    assert card["fit_reason"].startswith("Weekly drop-in")


def test_unscored_activity_has_no_score(flow_ctx, new_parent):
    """A nil score must stay nil. If it degraded to 0.0 the client would render
    "0% Match", which reads as a terrible match rather than an unknown one."""
    parent = new_parent
    activity_id = _track(flow_ctx, parent, name="Library story time",
                         kid_name="Ben", activity_type="outing")
    card = _card(flow_ctx.get("/cos/plan/board", as_=parent).json(), activity_id)
    assert card is not None
    assert card.get("fit_score") in (None,), f"unscored activity got {card.get('fit_score')!r}"


def test_overlapping_activities_warn_each_other(flow_ctx, new_parent):
    """A trip that falls INSIDE a longer camp, for the same kid.

    This is the case the old signal missed: `competes_with` compared
    same-kid-same-week_start by string equality, so a 3-day trip inside a
    10-week camp looked like no conflict at all.
    """
    parent = new_parent
    camp = _track(flow_ctx, parent, name="YMCA Day Camp", kid_name="Lily",
                  activity_type="camp", start_date="2026-06-22",
                  end_date="2026-08-28", status="signed_up")
    trip = _track(flow_ctx, parent, name="Rialto Beach trip", kid_name="Lily",
                  activity_type="trip", start_date="2026-08-15",
                  end_date="2026-08-17", status="planned")

    board = flow_ctx.get("/cos/plan/board", as_=parent).json()
    camp_card, trip_card = _card(board, camp), _card(board, trip)
    assert camp_card and trip_card

    # Reciprocal: BOTH cards warn, each naming the other.
    camp_overlaps = camp_card.get("overlaps") or []
    trip_overlaps = trip_card.get("overlaps") or []
    assert [o["activity_id"] for o in camp_overlaps] == [trip], camp_overlaps
    assert [o["activity_id"] for o in trip_overlaps] == [camp], trip_overlaps

    # Exact wire shape the client decodes, and a server-rendered range.
    entry = camp_overlaps[0]
    assert set(entry) == {"activity_id", "name", "range"}, entry
    assert entry["name"] == "Rialto Beach trip"
    assert entry["range"], "the overlap range must be pre-rendered server-side"


def test_a_declined_activity_conflicts_with_nothing(flow_ctx, new_parent):
    parent = new_parent
    camp = _track(flow_ctx, parent, name="Sports Mini Camp", kid_name="Ben",
                  activity_type="camp", start_date="2026-07-06",
                  end_date="2026-07-31", status="signed_up")
    _track(flow_ctx, parent, name="Passed-on art camp", kid_name="Ben",
           activity_type="camp", start_date="2026-07-13",
           end_date="2026-07-17", status="declined")

    card = _card(flow_ctx.get("/cos/plan/board", as_=parent).json(), camp)
    assert card is not None
    assert (card.get("overlaps") or []) == [], (
        "a declined activity is still raising an overlap warning"
    )


def test_checklist_carries_completed_todos(flow_ctx, new_parent):
    """`todos` = the whole checklist (with `done`); `open_todos` = open only.

    They are deliberately different lists: the "Still to do" block renders the
    full history struck through, while next_step and the follow-ups list depend
    on open_todos staying narrow.
    """
    parent = new_parent
    activity_id = _track(flow_ctx, parent, name="Swim lessons", kid_name="Lily",
                         activity_type="extracurricular", status="signed_up")

    made = []
    for title in ("Register Lily", "Forward the confirmation email"):
        resp = flow_ctx.post("/cos/todos",
                             json={"user_id": parent.user_id, "title": title,
                                   "activity_id": activity_id}, as_=parent)
        assert resp.status_code == 200, resp.text
        made.append(resp.json()["id"])

    done_id = made[0]
    # The /cos/* PATCH bodies carry user_id and are authorized against the
    # bearer (authorize_user_match) — omitting it is a 422, not a 401.
    patched = flow_ctx.patch(f"/cos/todos/{done_id}",
                             json={"user_id": parent.user_id, "status": "done"},
                             as_=parent)
    assert patched.status_code == 200, patched.text

    card = _card(flow_ctx.get("/cos/plan/board", as_=parent).json(), activity_id)
    assert card is not None

    todos = card.get("todos")
    assert todos is not None, "board card is missing `todos` — the key iOS decodes"
    by_title = {t["title"]: t["done"] for t in todos}
    # A subset assertion, not equality: tracking straight into `signed_up` fires
    # lifecycle.on_created, which seeds its own "forward the confirmation" to-do.
    # That is correct behaviour, so the test must not forbid extra rows.
    assert by_title.get("Register Lily") is True, by_title
    assert by_title.get("Forward the confirmation email") is False, by_title

    open_titles = [t["title"] for t in card["open_todos"]]
    assert "Register Lily" not in open_titles, (
        f"open_todos must stay open-only, got {open_titles}"
    )
    assert "Forward the confirmation email" in open_titles, open_titles
    # The full list is strictly larger than the open one — that difference IS
    # the feature (the checklist shows finished work struck through).
    assert len(todos) > len(card["open_todos"])
