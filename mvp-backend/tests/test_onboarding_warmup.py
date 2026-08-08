"""First-run agent warm-up (app/onboarding_warmup.py).

Hermetic: a tempfile DuckDBStorage plus INJECTED step functions, so no LLM and
no network. What's locked here:

  • enqueue -> claim -> finalize, with the run reaching a terminal state and the
    ring landing at 100.
  • idempotent re-run — a restart that re-queues a half-done run does NOT redo
    finished beats, and the real step_plan/upsert_coach_nudge writes don't
    duplicate on a second pass.
  • THE HARD RULE: a step that raises, and a step that never returns, each get
    marked `failed` WITHOUT blocking the steps after them or the run's terminal
    state. A parent stuck behind a spinner is worse than an unpersonalised Home.
  • the HTTP surface: auth, cross-user 403/404, the poll payload shape.

TestClient note: the context exit closes the storage singleton, so every
TestClient block rebuilds server.storage_backend in a `finally` — the
_reconnect_shared_storage idiom from tests/test_onboarding_seed_contract.py.
Without it, LATER test modules fail with "Connection already closed".
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "warmup.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.onboarding_warmup import (  # noqa: E402
    DONE,
    FAILED,
    PENDING,
    SKIPPED,
    STEP_ACCOUNT,
    STEP_COACH,
    STEP_FAMILY,
    STEP_KEYS,
    STEP_PLAN,
    OnboardingWarmupWorker,
    init_worker,
    initial_steps,
    overall_percent,
    status_payload,
    step_account,
    step_plan,
)


def _reconnect_shared_storage(server):
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "warmup.duckdb")


def _ok(name):
    def _fn(storage, user_id, ctx):
        ctx.setdefault("ran", []).append(name)
        return {"ran": name}
    return _fn


def _all_ok():
    return {key: _ok(key) for key in STEP_KEYS}


# ── the happy path ───────────────────────────────────────────────────

def test_enqueue_claim_finalize(store):
    result = store.enqueue_warmup_run(user_id="u1", steps=initial_steps(), context={})
    assert result["deduped"] is False
    run_id = result["run_id"]

    claimed = store.claim_next_queued_warmup_run()
    assert claimed["id"] == run_id
    assert claimed["status"] == "running"
    assert claimed["started_at"] is not None

    OnboardingWarmupWorker(store, _all_ok()).process_run(claimed)

    run = store.get_warmup_run(run_id)
    assert run["status"] == "done"
    assert run["finished_at"] is not None
    assert [s["key"] for s in run["steps"]] == STEP_KEYS
    assert {s["state"] for s in run["steps"]} == {DONE}
    assert run["result"]["failed_steps"] == []

    payload = status_payload(run)
    assert payload["percent"] == 100
    # Stable keys + the human labels the ring renders, in beat order.
    assert [s["label"] for s in payload["steps"]] == [
        "Getting to know your family",
        "Bringing your coach up to speed",
        "Sketching your first plan",
        "Securing your family's space",
    ]


def test_enqueue_dedupes_in_flight_run(store):
    first = store.enqueue_warmup_run(user_id="u1", steps=initial_steps(), context={})
    again = store.enqueue_warmup_run(user_id="u1", steps=initial_steps(), context={})
    assert again["deduped"] is True and again["run_id"] == first["run_id"]

    # Once terminal, a fresh enqueue is a NEW run (a reinstall can warm up again).
    store.claim_next_queued_warmup_run()
    store.finalize_warmup_run_if_running(first["run_id"], status="done")
    third = store.enqueue_warmup_run(user_id="u1", steps=initial_steps(), context={})
    assert third["deduped"] is False and third["run_id"] != first["run_id"]


def test_percent_is_monotonic_and_lands_at_100():
    steps = initial_steps()
    assert overall_percent(steps, "queued") == 0
    steps[0]["state"] = "running"
    assert overall_percent(steps, "running") == 13
    steps[0]["state"] = DONE
    assert overall_percent(steps, "running") == 25
    steps[1]["state"] = FAILED  # a failure still advances the ring
    assert overall_percent(steps, "running") == 50
    # Terminal always lands, whatever the steps say.
    assert overall_percent(steps, "done") == 100


# ── the hard rule: a failing/stalling step never blocks ──────────────

def test_failing_step_does_not_block_the_others_or_the_run(store):
    """One beat raises. The beats AFTER it still run, the run still reaches a
    terminal state, and the ring still lands at 100."""
    run_id = store.create_warmup_run(user_id="u1", steps=initial_steps(), context={})
    claimed = store.claim_next_queued_warmup_run()

    def _boom(storage, user_id, ctx):
        raise RuntimeError("openai timed out")

    funcs = _all_ok()
    funcs[STEP_COACH] = _boom
    OnboardingWarmupWorker(store, funcs).process_run(claimed)

    run = store.get_warmup_run(run_id)
    assert run["status"] == "done", "a failed step must not leave the run non-terminal"
    assert run["finished_at"] is not None
    by_key = {s["key"]: s for s in run["steps"]}
    assert by_key[STEP_COACH]["state"] == FAILED
    assert "openai timed out" in by_key[STEP_COACH]["error"]
    # Everything else — including the beats AFTER the failure — still ran.
    assert by_key[STEP_FAMILY]["state"] == DONE
    assert by_key[STEP_PLAN]["state"] == DONE
    assert by_key[STEP_ACCOUNT]["state"] == DONE
    assert run["result"]["failed_steps"] == [STEP_COACH]
    assert status_payload(run)["percent"] == 100


def test_stalled_step_times_out_and_the_run_still_lands(store):
    """A step that never returns is abandoned at its budget — the parent is not
    held behind it."""
    store.create_warmup_run(user_id="u1", steps=initial_steps(), context={})
    claimed = store.claim_next_queued_warmup_run()

    release = threading.Event()

    def _stall(storage, user_id, ctx):
        release.wait(30)  # far longer than the step budget
        return {}

    funcs = _all_ok()
    funcs[STEP_FAMILY] = _stall

    started = time.time()
    try:
        OnboardingWarmupWorker(store, funcs, step_timeout=0.3).process_run(claimed)
    finally:
        release.set()
    elapsed = time.time() - started

    assert elapsed < 10, "the run must not wait on a stalled step"
    run = store.get_warmup_run(claimed["id"])
    assert run["status"] == "done"
    by_key = {s["key"]: s for s in run["steps"]}
    assert by_key[STEP_FAMILY]["state"] == FAILED
    assert "timed out" in by_key[STEP_FAMILY]["error"]
    assert by_key[STEP_ACCOUNT]["state"] == DONE


def test_finalize_is_conditional_so_a_cancel_sticks(store):
    """The cancel-clobber guard: a worker that finishes after the parent
    cancelled must not resurrect the run to done."""
    run_id = store.create_warmup_run(user_id="u1", steps=initial_steps(), context={})
    claimed = store.claim_next_queued_warmup_run()
    store.update_warmup_run(run_id, status="canceled", finished=True)

    OnboardingWarmupWorker(store, _all_ok()).process_run(claimed)
    assert store.get_warmup_run(run_id)["status"] == "canceled"


# ── idempotency ──────────────────────────────────────────────────────

def test_requeue_after_restart_does_not_redo_finished_beats(store):
    """The startup sweeper re-queues a run a restart left 'running'. The re-run
    resumes at the first unfinished beat instead of repeating the work."""
    run_id = store.create_warmup_run(user_id="u1", steps=initial_steps(), context={})
    claimed = store.claim_next_queued_warmup_run()

    # Simulate a crash halfway: family done, the rest still pending.
    steps = claimed["steps"]
    steps[0]["state"] = DONE
    steps[0]["detail"] = {"kid_count": 1}
    store.update_warmup_run(run_id, steps=steps)

    assert store.requeue_stale_warmup_runs() == 1
    assert store.get_warmup_run(run_id)["status"] == "queued"

    reclaimed = store.claim_next_queued_warmup_run()
    assert reclaimed["id"] == run_id
    calls = []
    funcs = {}
    for key in STEP_KEYS:
        def _fn(storage, user_id, ctx, _k=key):
            calls.append(_k)
            return {}
        funcs[key] = _fn
    OnboardingWarmupWorker(store, funcs).process_run(reclaimed)

    assert STEP_FAMILY not in calls, "an already-done beat must not be redone"
    assert calls == [STEP_COACH, STEP_PLAN, STEP_ACCOUNT]
    run = store.get_warmup_run(run_id)
    assert run["status"] == "done"
    assert run["steps"][0]["detail"] == {"kid_count": 1}, "prior detail survived"


def test_step_plan_is_idempotent_and_seeds_the_board(store):
    """The real plan step: age/ZIP-derived considerations land in the board's
    Considering stage, and running it twice does not duplicate them."""
    from app.cos import lifecycle
    from app.profiling import profiling_service

    user_id = "warmup-plan-user"
    profiling_service.update_parent_profile(user_id, {"name": "Greg", "postal_code": "98333"})
    profiling_service.update_child_profile(user_id, "Ben", {"name": "Ben", "age": 5.0})

    first = step_plan(store, user_id, {})
    assert first["considerations_seeded"] > 0
    assert first["postal_code"] == "98333"

    activities = store.list_tracked_activities(user_id)
    assert len(activities) == first["considerations_seeded"]
    assert all(a["kid_name"] == "Ben" for a in activities)
    assert all(lifecycle.stage_for(a["status"]) == "considering" for a in activities)

    second = step_plan(store, user_id, {})
    assert second["considerations_seeded"] == 0, "a re-run must not duplicate the board"
    assert len(store.list_tracked_activities(user_id)) == len(activities)

    profiling_service.remove_family(user_id)


def test_step_coach_persists_a_nudge_and_never_names_a_stranger(store, monkeypatch):
    """The real coach step against a stubbed model: the nudge is persisted for
    Home's COACH card, and a hallucinated child name is replaced with a real
    one before it can reach the parent."""
    import app.agent as agent_mod
    from app.onboarding_warmup import _NudgeDraft, step_coach
    from app.profiling import profiling_service

    user_id = "warmup-coach-user"
    profiling_service.update_parent_profile(user_id, {"name": "Greg"})
    profiling_service.update_child_profile(user_id, "Ben", {"name": "Ben", "age": 5.0})

    class _FakeLLM:
        def with_structured_output(self, schema):
            assert schema is _NudgeDraft
            return self

        def invoke(self, messages):
            assert any("Family profile" in m["content"] for m in messages)
            return _NudgeDraft(
                body="Ben's been practicing taking turns. Tonight, try trading who "
                     "picks the bedtime book.",
                kid_name="Nobody",  # the model invented a child
                cta_label=None,
            )

    monkeypatch.setattr(agent_mod, "llm", _FakeLLM())
    monkeypatch.setattr(agent_mod, "get_agent", lambda uid: object())

    detail = step_coach(store, user_id, {"run_id": "run-1"})
    assert detail["kid_name"] == "Ben", "an invented child must not reach the card"

    nudge = store.latest_coach_nudge(user_id)
    assert nudge["body"].startswith("Ben's been practicing")
    assert nudge["cta_label"] == "Try this with Ben"
    assert nudge["source"] == "warmup" and nudge["origin_id"] == "run-1"

    # No kids yet -> skipped, not failed (nothing to say, nothing to block on).
    assert step_coach(store, "warmup-coach-empty", {})["skipped"] is True

    profiling_service.remove_family(user_id)


def test_step_account_provisions_without_forging_legal_acceptance(store):
    """Account provisioning is idempotent; the legal beat REPORTS what's still
    pending and never records an acceptance the parent didn't make."""
    from app.profiling import profiling_service

    user_id = "warmup-account-user"
    profiling_service.update_parent_profile(user_id, {"name": "Greg"})

    detail = step_account(store, user_id, {})
    assert detail["account_provisioned"] is True
    assert isinstance(detail["pending_legal"], list)

    analytics_id = store.analytics_id_for(user_id)
    assert analytics_id
    step_account(store, user_id, {})
    assert store.analytics_id_for(user_id) == analytics_id, "provisioning must be idempotent"

    for slug in detail["pending_legal"]:
        assert store.latest_legal_acceptance(user_id, slug) is None, (
            "the warm-up must never record an acceptance on the parent's behalf"
        )

    profiling_service.remove_family(user_id)


def test_unregistered_step_is_skipped_not_stuck(store):
    store.create_warmup_run(user_id="u1", steps=initial_steps(), context={})
    claimed = store.claim_next_queued_warmup_run()
    OnboardingWarmupWorker(store, {STEP_FAMILY: _ok(STEP_FAMILY)}).process_run(claimed)

    run = store.get_warmup_run(claimed["id"])
    assert run["status"] == "done"
    states = {s["key"]: s["state"] for s in run["steps"]}
    assert states[STEP_FAMILY] == DONE
    assert states[STEP_COACH] == SKIPPED
    assert PENDING not in states.values()


def test_init_worker_sets_singleton(store):
    import app.onboarding_warmup as mod

    w = init_worker(store, step_funcs=_all_ok())
    assert mod.warmup_worker is w
    w.stop(timeout=0.1)


def test_coach_nudge_upsert_replaces_not_appends(store):
    store.upsert_coach_nudge(user_id="u1", body="first", kid_name="Ben", cta_label="Try this with Ben")
    store.upsert_coach_nudge(user_id="u1", body="second", kid_name="Ben")
    nudge = store.latest_coach_nudge("u1")
    assert nudge["body"] == "second"
    assert store.get_warmup_run("nope") is None
    rows = store._con.execute(
        "SELECT count(*) FROM coach_nudges WHERE user_id = 'u1'"
    ).fetchone()[0]
    assert rows == 1, "a warm-up re-run must not leave two 'first' nudges"


# ── HTTP surface ─────────────────────────────────────────────────────

def test_warmup_endpoints_require_auth_and_own_the_run():
    from fastapi.testclient import TestClient
    import app.server as server
    import app.onboarding_warmup as warmup_mod

    try:
        with TestClient(server.app) as client:
            # Keep the live worker out of it — the endpoints are what's under test.
            warmup_mod.warmup_worker = None

            user_id = "warmup-http-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            assert client.post("/onboarding/warmup", json={}).status_code == 401

            r = client.post("/onboarding/warmup", json={"user_id": user_id}, headers=auth)
            assert r.status_code == 200, r.text
            run_id = r.json()["run_id"]
            assert r.json()["status"] == "queued"

            # A body user_id that isn't the caller is rejected outright.
            assert client.post(
                "/onboarding/warmup", json={"user_id": "someone-else"}, headers=auth
            ).status_code == 403

            # Double-tap dedupes onto the same run.
            again = client.post("/onboarding/warmup", json={}, headers=auth).json()
            assert again["run_id"] == run_id and again["deduped"] is True

            got = client.get(f"/onboarding/warmup/{run_id}", headers=auth)
            assert got.status_code == 200, got.text
            body = got.json()
            assert body["run_id"] == run_id
            assert isinstance(body["percent"], int)
            assert [s["key"] for s in body["steps"]] == STEP_KEYS
            assert all(s["state"] == PENDING for s in body["steps"])

            assert client.get(f"/onboarding/warmup/{run_id}").status_code == 401
            assert client.get("/onboarding/warmup/does-not-exist", headers=auth).status_code == 404

            # Another parent cannot read this run. 404, not 403 — the resource
            # form of authorize_user_match refuses to leak that it exists.
            other = "warmup-http-other"
            otok = client.post("/auth/issue-token", json={"user_id": other}).json()["token"]
            assert client.get(
                f"/onboarding/warmup/{run_id}",
                headers={"Authorization": f"Bearer {otok}"},
            ).status_code == 404

            # The coach-nudge read Home binds to.
            assert client.get("/coach/nudge").status_code == 401
            assert client.get("/coach/nudge", headers=auth).json()["nudge"] is None
            server.storage_backend.upsert_coach_nudge(
                user_id=user_id, body="Ben's been practicing taking turns.",
                kid_name="Ben", cta_label="Try this with Ben",
            )
            nudge = client.get("/coach/nudge", headers=auth).json()["nudge"]
            assert nudge["body"].startswith("Ben's been")
            assert nudge["cta_label"] == "Try this with Ben"
    finally:
        _reconnect_shared_storage(server)


def test_warmup_stream_emits_progress_then_final():
    from fastapi.testclient import TestClient
    import app.server as server
    import app.onboarding_warmup as warmup_mod

    try:
        with TestClient(server.app) as client:
            warmup_mod.warmup_worker = None

            user_id = "warmup-stream-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            run_id = client.post(
                "/onboarding/warmup", json={}, headers=auth
            ).json()["run_id"]
            # Drive it to terminal so the stream closes promptly.
            server.storage_backend.claim_next_queued_warmup_run()
            OnboardingWarmupWorker(
                server.storage_backend, _all_ok()
            ).process_run(server.storage_backend.get_warmup_run(run_id))

            with client.stream(
                "GET", f"/onboarding/warmup/{run_id}/stream", headers=auth
            ) as resp:
                assert resp.status_code == 200
                frames = [line for line in resp.iter_lines() if line.startswith("data: ")]

            assert frames[-1] == "data: [DONE]"
            assert '"type": "final"' in frames[-2]
            assert '"percent": 100' in frames[-2]
    finally:
        _reconnect_shared_storage(server)


def test_warmup_deletes_with_the_family():
    """CLAUDE.md: deletes cascade. A purged family leaves no warm-up rows and no
    orphan coach nudge behind."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            user_id = "warmup-delete-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}
            client.post("/onboarding/warmup", json={}, headers=auth)
            server.storage_backend.upsert_coach_nudge(user_id=user_id, body="hi")

            counts = server.storage_backend.delete_family(
                user_id=user_id, actor="test"
            )["counts"]
            assert counts["onboarding_warmup_runs"] >= 1
            assert counts["coach_nudges"] >= 1
            assert server.storage_backend.latest_coach_nudge(user_id) is None
            assert server.storage_backend.list_warmup_runs(user_id) == []
    finally:
        _reconnect_shared_storage(server)
