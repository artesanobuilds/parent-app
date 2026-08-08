# flows/generated/test_onboarding_warmup_first_run.py
#
# @generated_from: specs/tier-1/onboarding-warmup-first-run.flow.yml
# @generated_at: 2026-08-07T00:00:00Z
# @modules: auth, profile, onboarding_warmup, coach, cos, content
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

# Make `lib` importable even when pytest is invoked from a different cwd.
HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.personas.new_parent import new_parent as _make_new_parent  # noqa: E402

pytestmark = pytest.mark.tier1

# The four beats, in the order the ring renders them. Stable client contract.
STEP_KEYS = ["family", "coach", "plan", "account"]
STEP_STATES = {"pending", "running", "done", "failed", "skipped"}
TERMINAL_STEP_STATES = {"done", "failed", "skipped"}
TERMINAL_RUN_STATES = {"done", "failed", "canceled"}

# The EXACT payload shape SwayApp.swift posts at the end of the funnel — kid
# `age` as a STRING, `household` as a string, `adults_in_household` as an int.
# Pinned in mvp-backend/tests/test_onboarding_seed_contract.py; mirrored here so
# a drift breaks the flow test too, at the real HTTP boundary iOS sees.
def _ios_seed_payload(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "parent_name": "Greg",
        "kids": [
            {"name": "Lily", "age": "12", "temperament": "", "pronouns": "", "grade_band": ""},
            {"name": "Ben", "age": "5", "temperament": "", "pronouns": "", "grade_band": ""},
        ],
        "household": "Single parent",
        "postal_code": "98333",
        "adults_in_household": 2,
    }


def _assert_family_shape(family: dict, where: str) -> None:
    """The coercion contract the three surfaces share."""
    parent = family["parent"]
    assert parent["name"] == "Greg", f"{where}: parent name lost"
    assert parent["postal_code"] == "98333", f"{where}: postal_code lost"
    # `household` (iOS) maps to `household_structure` (backend).
    assert parent["household_structure"] == "Single parent", \
        f"{where}: `household` did not map to `household_structure`: {parent!r}"
    assert parent["adults_in_household"] == 2, f"{where}: adults_in_household lost"
    assert isinstance(parent["adults_in_household"], int), \
        f"{where}: adults_in_household must stay an int, got {type(parent['adults_in_household'])}"

    children = family["children"]
    assert "Lily" in children and "Ben" in children, f"{where}: kids lost: {children!r}"
    # Kid `age` arrives as a STRING and must read back as a FLOAT — DuckDB
    # DOUBLE -> Swift Double?. An int here empties the list on iOS.
    for name, expected in (("Lily", 12.0), ("Ben", 5.0)):
        age = children[name]["age"]
        assert age == expected, f"{where}: {name} age {age!r} != {expected}"
        assert isinstance(age, float), \
            f"{where}: {name} age must coerce to float, got {type(age)} ({age!r})"


def _assert_status_payload(body: dict) -> None:
    """The wire shape the poll endpoint and the SSE stream both emit."""
    for key in ("run_id", "status", "percent", "steps", "result", "error"):
        assert key in body, f"warm-up status missing {key!r}: {sorted(body)}"

    percent = body["percent"]
    assert isinstance(percent, int) and not isinstance(percent, bool), \
        f"percent must be an int, got {type(percent)} ({percent!r})"
    assert 0 <= percent <= 100, f"percent out of range: {percent}"

    steps = body["steps"]
    assert isinstance(steps, list), f"steps must be a list, got {type(steps)}"
    assert [s["key"] for s in steps] == STEP_KEYS, \
        f"the four beats drifted (order is the client contract): {[s.get('key') for s in steps]}"
    for step in steps:
        for key in ("key", "label", "state", "detail", "error"):
            assert key in step, f"step {step.get('key')!r} missing {key!r}: {sorted(step)}"
        assert step["label"], f"step {step['key']!r} has no label to render"
        assert step["state"] in STEP_STATES, \
            f"step {step['key']!r} has unknown state {step['state']!r}"


def _poll_to_terminal(flow_ctx, parent, run_id: str, *, timeout_s: float = 150.0) -> dict:
    """Poll until the run is terminal, asserting the ring's invariants on EVERY
    sample: the endpoint keeps answering 200, the payload keeps its shape, and
    the percentage never ticks backwards. Returns the terminal payload."""
    seen: dict = {"last_percent": -1, "body": None}

    def _terminal() -> bool:
        resp = flow_ctx.get(f"/onboarding/warmup/{run_id}", as_=parent)
        assert resp.status_code == 200, \
            f"poll endpoint returned {resp.status_code} mid-flight: {resp.text}"
        body = resp.json()
        _assert_status_payload(body)
        assert body["run_id"] == run_id, f"poll returned a foreign run: {body['run_id']}"
        assert body["percent"] >= seen["last_percent"], (
            "the ring ticked BACKWARDS: "
            f"{seen['last_percent']} -> {body['percent']} (steps={body['steps']})"
        )
        seen["last_percent"] = body["percent"]
        seen["body"] = body
        return body["status"] in TERMINAL_RUN_STATES

    flow_ctx.wait_for(
        _terminal,
        timeout_s=timeout_s,
        interval_s=1.0,
        description="first-run warm-up reaches a terminal state",
    )
    return seen["body"]


def _assert_ring_landed(body: dict) -> dict:
    """THE HARD RULE: the ring must never trap the parent. A terminal run is
    always 100, every beat is terminal, and a failed beat is reported rather
    than blocking. Returns {step_key: step}."""
    assert body["status"] in TERMINAL_RUN_STATES, f"run not terminal: {body['status']!r}"
    assert body["percent"] == 100, \
        f"a terminal run must read 100 or the ring hangs; got {body['percent']} ({body})"

    by_key = {s["key"]: s for s in body["steps"]}
    stuck = [k for k, s in by_key.items() if s["state"] not in TERMINAL_STEP_STATES]
    assert not stuck, f"beats left non-terminal after the run finished: {stuck}"

    failed = [k for k, s in by_key.items() if s["state"] == "failed"]
    if failed:
        # The whole point of the feature: a bad beat degrades Home, it does not
        # block the parent behind a spinner.
        assert body["status"] == "done", \
            f"beats {failed} failed and dragged the RUN to {body['status']!r} — the ring traps the parent"
        assert body["percent"] == 100
        assert sorted(body["result"].get("failed_steps") or []) == sorted(failed), \
            f"result.failed_steps {body['result'].get('failed_steps')!r} does not name the failed beats {failed}"
        for key in failed:
            assert by_key[key]["error"], f"failed beat {key!r} carries no error string"
    return by_key


def _assert_nudge_well_formed(body: dict) -> dict | None:
    """`null` is a legitimate, expected value — the COACH card falls back to its
    empty state. A non-null nudge must be renderable."""
    assert "nudge" in body, f"/coach/nudge missing `nudge` key: {sorted(body)}"
    nudge = body["nudge"]
    if nudge is None:
        return None
    assert isinstance(nudge, dict), f"nudge must be an object or null, got {type(nudge)}"
    assert (nudge.get("body") or "").strip(), f"a non-null nudge needs a body: {nudge!r}"
    return nudge


def _board_activities(board: dict) -> list:
    assert "stages" in board, f"board missing `stages`: {sorted(board)}"
    out = []
    for stage in board["stages"]:
        assert "key" in stage and "activities" in stage, f"malformed stage: {stage!r}"
        out.extend(stage["activities"])
    return out


# ── the always-on flow ───────────────────────────────────────────────


def test_first_run_warmup_lands_and_fills_the_dashboard(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (seeds a family + enqueues a warm-up); skipped on prod")
    if flow_ctx.fault.available:
        pytest.skip(
            "the fault-injection backend runs an isolated empty DuckDB with no "
            "content library, so the FOR YOU half of this flow has nothing to "
            "rank; the degradation guarantee is covered by "
            "test_a_failed_beat_still_lands_the_ring in that env"
        )

    parent = new_parent  # /auth/issue-token already done by the fixture
    assert parent.token, "issuer returned an empty token"
    assert parent.user_id, "issuer returned no user_id"

    # ── the funnel's answers land, with the iOS coercions intact ────
    seed = flow_ctx.post("/profile/seed", json=_ios_seed_payload(parent.user_id), as_=parent)
    assert seed.status_code == 200, seed.text
    _assert_family_shape(seed.json(), "seed response")

    profile = flow_ctx.get("/profile", as_=parent)
    assert profile.status_code == 200, profile.text
    _assert_family_shape(profile.json(), "GET /profile round-trip")

    # ── the ring: enqueue ───────────────────────────────────────────
    enq = flow_ctx.post("/onboarding/warmup", json={"user_id": parent.user_id}, as_=parent)
    assert enq.status_code == 200, enq.text
    enq_body = enq.json()
    for key in ("run_id", "status", "deduped"):
        assert key in enq_body, f"enqueue missing {key!r}: {sorted(enq_body)}"
    run_id = enq_body["run_id"]
    assert run_id, "enqueue returned an empty run_id"
    assert enq_body["status"] == "queued", f"a fresh enqueue should be queued: {enq_body}"
    assert enq_body["deduped"] is False, f"nothing to dedupe onto for a fresh parent: {enq_body}"

    # A double-tapped ring must not stack a second run. (If the first run has
    # already finished by now, a NEW run is correct — dedupe is on in-flight
    # runs only — so this asserts the invariant that actually holds either way.)
    again = flow_ctx.post("/onboarding/warmup", json={"user_id": parent.user_id}, as_=parent)
    assert again.status_code == 200, again.text
    again_body = again.json()
    assert again_body.get("run_id"), f"second enqueue returned no run_id: {again_body}"
    if again_body["deduped"] is True:
        assert again_body["run_id"] == run_id, \
            f"a deduped enqueue must return the in-flight run, got {again_body['run_id']} != {run_id}"

    # ── another family cannot watch this ring ───────────────────────
    # The persona fixture is per-test, so mint a second family directly.
    stranger = _make_new_parent(flow_ctx)
    peek = flow_ctx.get(f"/onboarding/warmup/{run_id}", as_=stranger)
    assert peek.status_code == 404, \
        f"cross-family warm-up poll must 404 (no existence oracle); got {peek.status_code}"

    # ── the ring: poll to terminal ──────────────────────────────────
    terminal = _poll_to_terminal(flow_ctx, parent, run_id)
    by_key = _assert_ring_landed(terminal)

    # ── COACH card: well-formed whether or not a nudge exists ───────
    nudge_resp = flow_ctx.get("/coach/nudge", as_=parent)
    assert nudge_resp.status_code == 200, nudge_resp.text
    _assert_nudge_well_formed(nudge_resp.json())

    # ── PLAN board: the plan beat is deterministic + offline, so it
    #    must land, and the board must no longer be empty ────────────
    assert by_key["plan"]["state"] == "done", (
        "the `plan` beat is deterministic and offline (age-banded starters, no "
        f"network) — it must reach done, got {by_key['plan']!r}"
    )
    board_resp = flow_ctx.get("/cos/plan/board", as_=parent)
    assert board_resp.status_code == 200, board_resp.text
    board = board_resp.json()
    activities = _board_activities(board)
    assert activities, \
        "the plan beat ran but the board is still empty — the dashboard opens blank"
    stage_of = {s["key"]: s["activities"] for s in board["stages"]}
    assert stage_of["considering"], \
        f"starter considerations must land in Considering, got stages: " \
        f"{ {k: len(v) for k, v in stage_of.items()} }"
    # Nothing is auto-registered and nothing is auto-watched: no email/calendar
    # side effects may fire off the back of onboarding.
    assert len(stage_of["considering"]) == len(activities), \
        "the warm-up moved something past Considering — onboarding must not auto-register"
    assert not any(a.get("watching") for a in activities), \
        "the warm-up put a seeded consideration under email watch"

    # ── FOR YOU: never empty, even for a just-seeded family ─────────
    feed_resp = flow_ctx.get("/content/for-you", as_=parent, params={"limit": 5, "offset": 0})
    assert feed_resp.status_code == 200, feed_resp.text
    feed = feed_resp.json()
    for key in ("items", "total", "limit", "offset", "ranked", "signals"):
        assert key in feed, f"/content/for-you missing {key!r}: {sorted(feed)}"
    assert feed["limit"] == 5 and feed["offset"] == 0, \
        f"feed did not echo the requested window: {feed['limit']}/{feed['offset']}"
    assert isinstance(feed["ranked"], bool), f"`ranked` must be a bool, got {type(feed['ranked'])}"
    assert isinstance(feed["signals"], list) and all(isinstance(s, str) for s in feed["signals"]), \
        f"`signals` must be a list of strings: {feed['signals']!r}"
    assert isinstance(feed["total"], int) and feed["total"] >= 1, \
        f"the for-you feed must never be empty; total={feed['total']!r}"
    assert feed["items"], "the for-you feed returned zero items — Home's FOR YOU opens blank"
    assert len(feed["items"]) <= 5, f"feed ignored limit=5: {len(feed['items'])} items"
    for item in feed["items"]:
        for key in ("id", "category", "title"):
            assert key in item, \
                f"for-you item diverges from /content/articles' shape (missing {key!r}): {sorted(item)}"


# ── requires_openai: the generated nudge ─────────────────────────────


@pytest.mark.requires_openai
def test_warmup_coach_beat_writes_a_personalized_first_nudge(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; the coach nudge is a real model call")
    if flow_ctx.fault.available:
        pytest.skip(
            "fault-injection env points the backend at the mock OpenAI, which "
            "cannot produce a real structured nudge; run this against a real model"
        )

    parent = new_parent
    seed = flow_ctx.post("/profile/seed", json=_ios_seed_payload(parent.user_id), as_=parent)
    assert seed.status_code == 200, seed.text
    seeded_kids = set(seed.json()["children"].keys())

    enq = flow_ctx.post("/onboarding/warmup", json={"user_id": parent.user_id}, as_=parent)
    assert enq.status_code == 200, enq.text
    run_id = enq.json()["run_id"]

    terminal = _poll_to_terminal(flow_ctx, parent, run_id)
    by_key = _assert_ring_landed(terminal)

    coach = by_key["coach"]
    assert coach["state"] == "done", \
        f"with a real model the coach beat must land: {coach!r}"
    assert coach["detail"].get("nudge_id"), f"coach beat wrote no nudge_id: {coach!r}"

    nudge_resp = flow_ctx.get("/coach/nudge", as_=parent)
    assert nudge_resp.status_code == 200, nudge_resp.text
    nudge = _assert_nudge_well_formed(nudge_resp.json())
    assert nudge is not None, "the coach beat reported done but /coach/nudge is null"
    assert nudge.get("kid_name") in seeded_kids, (
        "the first nudge names a child this family does not have: "
        f"{nudge.get('kid_name')!r} not in {sorted(seeded_kids)}"
    )
    assert (nudge.get("cta_label") or "").strip(), \
        f"Home's COACH card needs a CTA label: {nudge!r}"


# ── fault-injected: the degradation guarantee, proven not assumed ────


@pytest.mark.requires_openai
def test_a_failed_beat_still_lands_the_ring(flow_ctx, new_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow; skipped on prod")
    if not flow_ctx.fault.available:
        pytest.skip(
            "fault injection unavailable (OPENAI_MOCK_CONTROL_URL unset); "
            "run via tools/run-fault-flows.sh"
        )

    parent = new_parent
    flow_ctx.register_cleanup("reset openai fault", lambda: flow_ctx.fault.reset())

    seed = flow_ctx.post("/profile/seed", json=_ios_seed_payload(parent.user_id), as_=parent)
    assert seed.status_code == 200, seed.text

    # Hard outage on the model the `coach` beat needs. The other three beats are
    # offline work and must be untouched.
    flow_ctx.fault("openai", "down")

    enq = flow_ctx.post("/onboarding/warmup", json={"user_id": parent.user_id}, as_=parent)
    assert enq.status_code == 200, enq.text
    run_id = enq.json()["run_id"]

    terminal = _poll_to_terminal(flow_ctx, parent, run_id)
    by_key = _assert_ring_landed(terminal)

    # The beat failed…
    assert by_key["coach"]["state"] == "failed", (
        "with the model forced down the coach beat should fail, got "
        f"{by_key['coach']!r} — is the fault reaching the backend?"
    )
    assert by_key["coach"]["error"], "a failed beat must carry an error for the logs"
    # …the run did not.
    assert terminal["status"] == "done", \
        f"a failed beat dragged the whole run to {terminal['status']!r}"
    assert terminal["percent"] == 100
    assert terminal["result"].get("failed_steps") == ["coach"], \
        f"result.failed_steps should name exactly the coach beat: {terminal['result']!r}"

    # …and the rest of the dashboard still got built.
    for key in ("family", "plan", "account"):
        assert by_key[key]["state"] == "done", \
            f"offline beat {key!r} should be unaffected by a model outage: {by_key[key]!r}"

    board = flow_ctx.get("/cos/plan/board", as_=parent)
    assert board.status_code == 200, board.text
    assert _board_activities(board.json()), \
        "the model outage cost the parent their seeded plan board too"

    # Home's COACH card degrades to its empty state — well-formed, not a 500.
    nudge_resp = flow_ctx.get("/coach/nudge", as_=parent)
    assert nudge_resp.status_code == 200, nudge_resp.text
    assert _assert_nudge_well_formed(nudge_resp.json()) is None, \
        "a failed coach beat must not leave a nudge behind"
