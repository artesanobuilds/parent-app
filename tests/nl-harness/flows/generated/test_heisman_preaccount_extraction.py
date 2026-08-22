# flows/generated/test_heisman_preaccount_extraction.py
#
# @generated_from: specs/tier-1/heisman-preaccount-extraction.flow.yml
# @generated_at: 2026-08-21T00:00:00Z
# @modules: onboarding_extract, auth, profile, cos
# @promoted_by: (none -- awaiting review)
#
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = pytest.mark.tier1


@dataclass
class _AnonSession:
    """Shim persona: carries the scope-only anon token as a bearer."""
    token: str


def _mint_anon(flow_ctx) -> _AnonSession:
    resp = flow_ctx.post("/onboarding/anon-session")
    assert resp.status_code == 200, (
        f"anon-session mint failed: {resp.status_code}: {resp.text[:200]}"
    )
    body = resp.json()
    assert "token" in body and "expires_in" in body, f"mint shape wrong: {sorted(body)}"
    assert isinstance(body["expires_in"], int) and body["expires_in"] > 0
    return _AnonSession(token=body["token"])


# The exact wire shapes the iOS AnonOnboardingService sends.
_SCRAP = (
    "Hi parents! Lily's swim lessons move to Tuesdays 4:15 pm at Northgate "
    "Aquatic Center starting next week. Bring goggles and a towel."
)


def test_anon_token_boundaries(flow_ctx, new_parent):
    """The security pair from the spec — the scope-only token opens exactly one
    door, and a user credential does not open it either."""
    anon = _mint_anon(flow_ctx)

    # No token → 401
    resp = flow_ctx.post("/onboarding/extract", json={"text": "x"})
    assert resp.status_code == 401, (
        f"extract without a token must 401, got {resp.status_code}: {resp.text[:200]}"
    )

    # A REAL user bearer → 401 (scope check — a user credential is not an
    # extraction credential).
    resp = flow_ctx.post("/onboarding/extract", json={"text": "x"}, as_=new_parent)
    assert resp.status_code == 401, (
        f"extract with a user bearer must 401, got {resp.status_code}: {resp.text[:200]}"
    )

    # The anon token is NOT a user credential: an authenticated endpoint
    # rejects it. (GET /profile requires a real bearer.)
    resp = flow_ctx.get("/profile", as_=anon)
    assert resp.status_code in (401, 403), (
        f"anon session token must not authenticate as a user; GET /profile "
        f"returned {resp.status_code}: {resp.text[:200]}"
    )

    # Input gates, with a VALID anon token: empty body 422, oversize text 413.
    resp = flow_ctx.post("/onboarding/extract", json={}, as_=anon)
    assert resp.status_code == 422, (
        f"empty extract body must 422, got {resp.status_code}: {resp.text[:200]}"
    )
    resp = flow_ctx.post(
        "/onboarding/extract", json={"text": "x" * 8_001}, as_=anon,
    )
    assert resp.status_code == 413, (
        f"oversize text must 413, got {resp.status_code}: {resp.text[:200]}"
    )


@pytest.mark.requires_openai
def test_extract_returns_structured_activities(flow_ctx):
    """The real model path: a realistic scrap comes back as structured
    activities. Content assertions stay loose (LLM output), shape stays strict."""
    anon = _mint_anon(flow_ctx)
    resp = flow_ctx.post("/onboarding/extract", json={"text": _SCRAP}, as_=anon)
    assert resp.status_code == 200, (
        f"extract failed: {resp.status_code}: {resp.text[:300]}"
    )
    activities = resp.json().get("activities")
    assert isinstance(activities, list) and len(activities) >= 1, (
        f"expected >=1 extracted activity, got {activities!r}"
    )
    for a in activities:
        for key in ("who", "what", "when", "where", "notes"):
            assert key in a, f"activity missing {key!r}: {sorted(a)}"
    # The scrap names one schedulable thing — swim lessons for Lily.
    joined = " ".join(str(a) for a in activities).lower()
    assert "swim" in joined, f"extraction lost the activity: {activities!r}"


def test_seed_carries_funnel_data_to_profile_and_board(flow_ctx, new_parent):
    """The post-signup handoff: topic + the parent's own to-dos + the (draft-
    carried) extraction results become profile fields and REAL board cards.
    Extraction output is inlined here exactly as the client draft would hold
    it, so this leg is deterministic (no LLM)."""
    seed = {
        "user_id": new_parent.user_id,
        "parent_name": "Greg",
        "kids": [
            {"name": "Lily", "age": "9", "temperament": "", "pronouns": "", "grade_band": ""},
        ],
        "topic": "A practice or lesson schedule",
        "parent_week_tasks": ["A gift to buy", "Date night"],
        "extracted_activities": [
            {
                "who": "Lily",
                "what": "Swim lessons",
                "when": "Tuesdays · 4:15 pm",
                "where": "Northgate Aquatic Center",
                "notes": "Bring goggles and a towel",
            },
            {
                "who": "Somebody Unknown",
                "what": "Peewee soccer",
                "when": "Saturdays · 9:00 am",
                "where": "Cedar Field",
                "notes": "",
            },
        ],
    }
    resp = flow_ctx.post("/profile/seed", json=seed, as_=new_parent)
    assert resp.status_code == 200, f"seed failed: {resp.status_code}: {resp.text[:300]}"

    # Profile: focus_topic + self_care_tasks landed (the silent-drop bug class).
    prof = flow_ctx.get("/profile", as_=new_parent)
    assert prof.status_code == 200, prof.text
    parent = prof.json()["parent"]
    assert parent.get("focus_topic") == "A practice or lesson schedule", (
        f"focus_topic lost: {parent.get('focus_topic')!r}"
    )
    assert parent.get("self_care_tasks") == ["A gift to buy", "Date night"], (
        f"self_care_tasks lost: {parent.get('self_care_tasks')!r}"
    )

    # Board: every card lands in a stage section; flatten and index by name.
    board = flow_ctx.get("/cos/plan/board", as_=new_parent)
    assert board.status_code == 200, board.text
    stages = board.json()["stages"]
    cards = [c for stage in stages for c in stage["activities"]]
    by_name = {c.get("name"): c for c in cards}

    # Parent's own to-dos: cards with NO kid attribution.
    for task in ("A gift to buy", "Date night"):
        assert task in by_name, f"parent task {task!r} missing from board: {sorted(by_name)}"
        assert by_name[task].get("kid_name") in (None, ""), (
            f"parent task {task!r} must have no kid, got {by_name[task].get('kid_name')!r}"
        )

    # Extracted activity with a matching kid: attributed to Lily, detail kept.
    assert "Swim lessons" in by_name, f"extracted activity missing: {sorted(by_name)}"
    swim = by_name["Swim lessons"]
    assert swim.get("kid_name") == "Lily", f"kid match failed: {swim.get('kid_name')!r}"
    swim_blob = str(swim)
    assert "4:15" in swim_blob and "Northgate" in swim_blob, (
        "extraction schedule/location detail lost on the board card"
    )

    # Extracted activity with an unknown `who`: still lands, family-wide.
    assert "Peewee soccer" in by_name, f"unmatched activity missing: {sorted(by_name)}"
    assert by_name["Peewee soccer"].get("kid_name") in (None, ""), (
        f"unknown who must not invent a kid: {by_name['Peewee soccer'].get('kid_name')!r}"
    )
