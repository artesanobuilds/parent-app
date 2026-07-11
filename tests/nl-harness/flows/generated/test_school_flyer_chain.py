# flows/generated/test_school_flyer_chain.py
#
# @generated_from: specs/tier-1/school-flyer-chain.flow.yml
# @generated_at: 2026-07-11T00:00:00Z
# @modules: ingest, cos
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = [pytest.mark.tier1, pytest.mark.requires_openai]

NEWSLETTER = """LINCOLN PTA WEEKLY — WEEK OF OCT 5
1) PICTURE DAY is Friday Oct 9 — order forms due Wed Oct 7.
2) FALL FUNDRAISER kicks off Monday: cookie dough catalogs go home, orders close Oct 30.
3) FIELD TRIP: 4th grade to the Exploratorium Nov 3 — permission slips due Oct 23.
4) SPIRIT WEEK Oct 12-16: Monday = pajama day, Friday = school colors!"""

WATCHED = {"signed_up", "confirmed"}


def test_newsletter_becomes_typed_school_items(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (creates activities/todos); skipped on prod")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; extraction would spend tokens")

    parent = existing_parent

    resp = flow_ctx.post(
        "/ingest/text",
        json={"user_id": parent.user_id, "text": NEWSLETTER, "source": "paste"},
        as_=parent,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "artifact_id" in body and "items" in body and "parked" in body
    assert len(body["items"]) >= 2, f"expected a multi-item extraction: {len(body['items'])}"

    # Blast-radius law: nothing lands WATCHED off an extraction.
    acts = flow_ctx.get("/cos/activities", as_=parent).json()["activities"]
    created_ids = {i["created"]["activity_id"] for i in body["items"]
                   if i["created"]["activity_id"]}
    created = [a for a in acts if a["id"] in created_ids]
    assert created, "extraction created no activities"
    assert all(a["status"] not in WATCHED for a in created), created

    # Typed cards on the board.
    board = flow_ctx.get("/cos/plan/board", as_=parent).json()
    cards = [a for s in board["stages"] for a in s["activities"] if a["id"] in created_ids]
    assert any(a["activity_type"] == "school_event" for a in cards), (
        f"no school_event card: {[(a['name'], a['activity_type']) for a in cards]}"
    )

    # The task chain produced typed to-dos (form/payment among them).
    todos = flow_ctx.get("/cos/todos", as_=parent).json()["todos"]
    chain_kinds = {t.get("kind") for t in todos if t.get("activity_id") in created_ids}
    assert chain_kinds & {"form", "payment"}, f"no typed chain to-dos: {chain_kinds}"
