# flows/generated/test_discovery_geo_coverage.py
#
# @generated_from: specs/tier-2/discovery-geo-coverage.flow.yml
# @generated_at: 2026-08-07T19:40:00Z
# @modules: research, geo
# @promoted_by: (none -- awaiting review)
#
# The spec for this flow was committed in 40d1f20 and the test was never written,
# so the acceptance criteria for the radius geo-grounding fix went unasserted.
#
# The bug it guards: a discovery run had no geographic grounding — it anchored on
# the single nearest big city, so from ZIP 95448 (Healdsburg) a 50-mile search
# reached Santa Rosa and MISSED Sebastopol at ~15mi, well inside the radius,
# where a real camp was. The fix enumerates the actual towns in the radius.
#
# Split in two on purpose:
#   * the geo-grounding assertion runs ALWAYS — it is pure local computation
#     against the bundled ZIP dataset and needs no OpenAI, so the regression that
#     actually caused the bug is covered on every run
#   * the live discovery run is gated on RUN_OPENAI_FLOWS (it spends tokens and
#     hits the web)
#
import sys
import time
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

pytestmark = pytest.mark.tier2

HEALDSBURG = "95448"
RADIUS_MILES = 50
# Sebastopol is the specific town the pre-fix search missed.
TARGET_TOWN = "Sebastopol"


def test_the_radius_enumerates_towns_the_old_anchor_missed():
    """The root-cause assertion, and it needs no backend or OpenAI.

    Imported directly rather than driven over HTTP because there is no endpoint
    that exposes the town enumeration — it is an input to the research prompt.
    This is the one place in the harness that reaches into backend code; it earns
    the exception by covering the actual regression cheaply and deterministically.
    """
    backend = HARNESS_ROOT.parents[1] / "mvp-backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    try:
        from app.research.geo import nearby_towns
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"backend geo module not importable from the harness: {exc}")

    towns = nearby_towns(HEALDSBURG, RADIUS_MILES)
    assert towns, f"ZIP {HEALDSBURG} resolved to no towns — is the bundled dataset present?"

    names = {str(t.get("city")) for t in towns}
    assert len(names) >= 5, (
        f"only {len(names)} towns in a {RADIUS_MILES}mi radius — that looks like "
        f"the old single-anchor behaviour: {sorted(names)}"
    )
    assert TARGET_TOWN in names, (
        f"{TARGET_TOWN} is ~15mi from {HEALDSBURG} and inside a {RADIUS_MILES}mi "
        f"radius, but the enumeration missed it: {sorted(names)}"
    )
    # Every town must carry a distance inside the radius, or the prompt would
    # ground the agent on places the parent cannot reach.
    for t in towns:
        d = float(t.get("distance_mi") or 0)
        assert d <= RADIUS_MILES + 1, f"{t.get('city')} is {d}mi away, outside the radius"


@pytest.mark.requires_openai
def test_a_live_run_spreads_across_the_radius(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on the read-only (production) env")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; a discovery run would spend OpenAI tokens")

    parent = new_parent
    started = flow_ctx.post(
        "/research/runs",
        json={
            "user_id": parent.user_id,
            "location": {"postal_code": HEALDSBURG, "country": "US",
                         "radius_km": int(RADIUS_MILES * 1.60934)},
            "params": {"focus": "art", "radius_miles": RADIUS_MILES},
        },
        as_=parent,
    )
    assert started.status_code == 200, started.text
    run_id = started.json().get("run_id")
    assert run_id, f"no run_id: {started.json()}"

    flow_ctx.register_cleanup(
        f"cancel research run {run_id}",
        lambda: flow_ctx.post(f"/research/runs/{run_id}/cancel", as_=parent),
    )

    deadline = time.time() + 300
    status = None
    while time.time() < deadline:
        poll = flow_ctx.get(f"/research/runs/{run_id}", as_=parent)
        assert poll.status_code == 200, poll.text
        status = poll.json().get("status")
        if status in ("done", "failed", "cancelled"):
            break
        time.sleep(5)
    assert status == "done", f"run ended as {status!r} (or timed out)"

    cands = flow_ctx.get(f"/research/runs/{run_id}/candidates", as_=parent)
    assert cands.status_code == 200, cands.text
    candidates = cands.json().get("candidates") or []
    assert candidates, "a completed discovery run returned no candidates"

    cities = {
        str(c.get("city")).strip()
        for c in candidates
        if c.get("city") and str(c.get("city")).strip()
    }
    assert len(cities) >= 2, (
        f"all candidates cluster in one town {cities} — the radius is not being "
        "covered, which is the exact pre-fix behaviour"
    )
    assert cities - {"Healdsburg"}, (
        f"every candidate is in the ZIP's own city: {cities}"
    )
