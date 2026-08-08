"""Activity lifecycle (app/cos/lifecycle.py) + the board endpoint + the
register-transition side effects. Offline — no network, no LLM.

Covers the plan's verification list: stage mapping, next-step CTAs, the board
contract, enter-WATCHED side effects (instant sync run + seeded TYPED to-dos,
idempotent, Gmail-aware), typed materialize to-dos, and the no-drift guarantee
(the three old grouping sites import lifecycle).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", tempfile.mktemp(suffix=".duckdb"))

from app.cos import lifecycle  # noqa: E402


# ── Stage mapping ────────────────────────────────────────────────────

@pytest.mark.parametrize("status,todos,stage", [
    ("exploring", 0, "considering"),
    ("interested", 0, "considering"),
    ("reference", 0, "considering"),
    (None, 0, "considering"),
    ("something-unknown", 0, "considering"),
    ("planned", 0, "to_register"),
    ("signed_up", 1, "registered"),
    ("signed_up", 0, "all_set"),
    # The review fix: confirmed with an open to-do must NOT hide in All set.
    ("confirmed", 1, "registered"),
    ("confirmed", 0, "all_set"),
    ("done", 3, "all_set"),
    ("pending_eligibility", 0, "blocked"),
    ("waitlisted", 0, "blocked"),
    ("declined", 0, "declined"),
])
def test_stage_for(status, todos, stage):
    assert lifecycle.stage_for(status, todos) == stage


def test_entered_watched_transitions():
    assert lifecycle.entered_watched("planned", "signed_up")
    assert lifecycle.entered_watched("exploring", "confirmed")
    assert lifecycle.entered_watched(None, "signed_up")  # created straight into it
    assert not lifecycle.entered_watched("signed_up", "confirmed")  # within group
    assert not lifecycle.entered_watched("confirmed", "declined")
    assert not lifecycle.entered_watched("planned", "planned")


def test_planned_is_decided_not_undecided():
    assert "planned" not in lifecycle.UNDECIDED
    assert "planned" not in lifecycle.WATCHED


# ── Next step (self-documenting CTAs) ────────────────────────────────

def test_next_step_labels_state_consequences():
    plan = lifecycle.next_step({"id": "x", "name": "Art Camp", "status": "exploring"}, [])
    assert plan["action"] == "plan" and plan["label"] == "We'll do it"

    reg = lifecycle.next_step(
        {"id": "x", "name": "Art Camp", "status": "planned", "signup_url": "http://x"}, [])
    assert reg["action"] == "register" and reg["url"] == "http://x"
    assert "watch" in reg["hint"].lower()  # the consequence is stated up front

    no_url = lifecycle.next_step({"id": "x", "name": "Art Camp", "status": "planned"}, [])
    assert no_url["action"] == "mark_registered"

    todo = {"id": "t9", "title": "Pay $450 by Jun 1", "kind": "payment", "status": "open"}
    pay = lifecycle.next_step({"id": "x", "name": "Art Camp", "status": "signed_up"}, [todo])
    assert pay["action"] == "complete_todo" and pay["todo_id"] == "t9"
    assert pay["label"] == "Pay $450 by Jun 1"


def test_todo_ordering_dated_payment_first():
    todos = [
        {"id": "a", "title": "generic", "kind": "task", "status": "open"},
        {"id": "b", "title": "Pay", "kind": "payment", "status": "open", "due_date": "2026-06-01"},
        {"id": "c", "title": "Form", "kind": "form", "status": "open"},
    ]
    step = lifecycle.next_step({"id": "x", "name": "C", "status": "signed_up"}, lifecycle._sort_todos(todos))
    assert step["todo_id"] == "b"  # dated payment wins


# ── Board building (the cross-surface contract) ──────────────────────

def test_build_board_contract():
    activities = [
        {"id": "a1", "name": "Art", "status": "exploring"},
        {"id": "a2", "name": "Swim", "status": "planned", "signup_url": "http://s"},
        {"id": "a3", "name": "Rock", "status": "signed_up",
         "contact": {"email": "hi@rock.com"}},
        {"id": "a4", "name": "Chess", "status": "confirmed"},   # no open todos → all set
        {"id": "a5", "name": "Farm", "status": "declined"},
    ]
    todos = [
        {"id": "t1", "activity_id": "a3", "status": "open", "kind": "payment", "title": "Pay $200"},
        {"id": "t2", "activity_id": "a3", "status": "done", "kind": "form", "title": "Old form"},
        {"id": "t3", "activity_id": None, "status": "open", "kind": "task", "title": "unlinked"},
    ]
    board = lifecycle.build_board(activities, todos, gmail_connected=True)
    assert board["gmail_connected"] is True
    by = {s["key"]: s for s in board["stages"]}
    # Contract: every stage present, in order, with title + blurb.
    assert [s["key"] for s in board["stages"]] == [
        "considering", "to_register", "registered", "all_set", "blocked", "declined"]
    assert all(s["title"] and s["blurb"] for s in board["stages"])
    assert [a["id"] for a in by["considering"]["activities"]] == ["a1"]
    assert [a["id"] for a in by["to_register"]["activities"]] == ["a2"]
    assert [a["id"] for a in by["registered"]["activities"]] == ["a3"]
    assert [a["id"] for a in by["all_set"]["activities"]] == ["a4"]
    rock = by["registered"]["activities"][0]
    assert [t["id"] for t in rock["open_todos"]] == ["t1"]  # done todo excluded
    assert rock["next_step"]["action"] == "complete_todo"
    assert rock["watching"] is True and rock["watchable"] is True
    chess = by["all_set"]["activities"][0]
    assert chess["watchable"] is False  # no contact email — client asks for it


# ── Enter-WATCHED side effects (storage-backed) ──────────────────────

@pytest.fixture()
def store(tmp_path):
    from app.duckdb_storage import DuckDBStorage
    return DuckDBStorage(db_path=tmp_path / "lifecycle.duckdb")


def test_on_enter_watched_seeds_typed_todos_and_is_idempotent(store):
    uid = "life-user"
    aid = store.track_activity(uid, name="Art Camp", status="planned",
                               price_amount=450.0, kid_name="Ceiba")
    activity = store.get_tracked_activity(aid)

    result = lifecycle.on_enter_watched(store, uid, activity)
    todos = [t for t in store.list_todos(uid) if t.get("activity_id") == aid]
    kinds = sorted(t["kind"] for t in todos)
    # Gmail NOT connected → payment todo + the "forward the confirmation" action.
    assert kinds == ["action", "payment"], todos
    assert result["sync_enqueued"] is False  # no Gmail → no junk run
    pay = next(t for t in todos if t["kind"] == "payment")
    assert "450" in pay["title"]

    # Re-entering must not double-seed.
    lifecycle.on_enter_watched(store, uid, activity)
    again = [t for t in store.list_todos(uid) if t.get("activity_id") == aid]
    assert len(again) == len(todos)


def test_on_enter_watched_no_price_no_payment_todo(store):
    uid = "life-user2"
    aid = store.track_activity(uid, name="Free Camp", status="planned")
    lifecycle.on_enter_watched(store, uid, store.get_tracked_activity(aid))
    kinds = [t["kind"] for t in store.list_todos(uid) if t.get("activity_id") == aid]
    assert "payment" not in kinds


def test_on_enter_declined_dismisses_only_that_activitys_open_todos(store):
    uid = "decline-user"
    aid = store.track_activity(uid, name="Art Camp", status="signed_up", price_amount=450.0)
    other = store.track_activity(uid, name="Swim", status="signed_up")
    store.add_todo(uid, title="Pay $450", activity_id=aid, kind="payment")
    done_id = store.add_todo(uid, title="Old form", activity_id=aid, kind="form")
    store.update_todo(done_id, status="done")
    store.add_todo(uid, title="Other camp todo", activity_id=other, kind="action")

    lifecycle.on_enter_declined(store, uid, store.get_tracked_activity(aid))

    by_title = {t["title"]: t["status"] for t in store.list_todos(uid)}
    assert by_title["Pay $450"] == "dismissed"      # open → dismissed
    assert by_title["Old form"] == "done"           # done untouched
    assert by_title["Other camp todo"] == "open"    # other activity untouched


def test_entered_declined_transitions():
    assert lifecycle.entered_declined("signed_up", "declined")
    assert lifecycle.entered_declined("exploring", "declined")
    assert not lifecycle.entered_declined("declined", "declined")
    assert not lifecycle.entered_declined("declined", "exploring")  # Reconsider


def test_delete_tracked_activity_cascades(store):
    uid = "cascade-user"
    aid = store.track_activity(uid, name="Art Camp", status="signed_up")
    store.add_todo(uid, title="Pay", activity_id=aid, kind="payment")
    cal_id = store.add_calendar_entry(
        uid, title="Art Camp", activity_id=aid, kind="camp", week_start="2026-06-15")
    store.add_logistics_assignment(
        uid, week_start="2026-06-15", kid_name="Ceiba", task="pickup",
        calendar_entry_id=cal_id, status="gap")

    store.delete_tracked_activity(aid)

    assert store.get_tracked_activity(aid) is None
    assert [t for t in store.list_todos(uid) if t.get("activity_id") == aid] == []
    assert [e for e in store.list_calendar_entries(uid) if e.get("activity_id") == aid] == []
    assert [l for l in store.list_logistics_assignments(uid)
            if l.get("calendar_entry_id") == cal_id] == []


def test_reset_plan_wipes_plan_but_keeps_profile(store):
    uid = "reset-user"
    store.track_activity(uid, name="Art Camp", status="signed_up")
    store.add_todo(uid, title="Pay", kind="payment")
    store.add_calendar_entry(uid, title="Camp", kind="camp", week_start="2026-06-15")
    counts = store.reset_plan(user_id=uid, actor=uid)
    assert counts["tracked_activities"] == 1
    assert counts["todo_items"] == 1
    assert counts["calendar_entries"] == 1
    assert store.list_tracked_activities(uid) == []
    assert store.list_todos(uid) == []
    assert store.list_calendar_entries(uid) == []
    # Another user's plan is untouched.
    other_aid = store.track_activity("other-user", name="Theirs", status="exploring")
    store.reset_plan(user_id=uid, actor=uid)
    assert store.get_tracked_activity(other_aid) is not None


# ── HTTP: PATCH transition + board endpoint ──────────────────────────

def test_patch_register_hook_and_board_endpoint(tmp_path):
    from fastapi.testclient import TestClient
    from app.duckdb_storage import DuckDBStorage
    import app.server as server
    prev = server.storage_backend
    server.storage_backend = DuckDBStorage(db_path=str(tmp_path / "board.duckdb"))
    try:
        with TestClient(server.app) as client:
            uid = "board-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            r = client.post("/cos/activities/track", headers=auth, json={
                "user_id": uid, "name": "Sebastopol Arts", "price_amount": 300.0,
            })
            aid = r.json()["id"]

            # Considering → planned → signed_up via PATCH (the UI path).
            client.patch(f"/cos/activities/{aid}", headers=auth,
                         json={"user_id": uid, "status": "planned"})
            r = client.patch(f"/cos/activities/{aid}", headers=auth,
                             json={"user_id": uid, "status": "signed_up"})
            assert r.status_code == 200

            board = client.get("/cos/plan/board", headers=auth).json()
            by = {s["key"]: s["activities"] for s in board["stages"]}
            # Register hook seeded a payment todo → it's under "registered".
            assert [a["id"] for a in by["registered"]] == [aid]
            entry = by["registered"][0]
            assert any(t["kind"] == "payment" for t in entry["open_todos"])
            assert entry["next_step"]["action"] == "complete_todo"
            # An email-sync run was NOT enqueued (no Gmail connected).
            runs = [r for r in server.storage_backend.list_email_sync_runs()
                    if r.get("user_id") == uid]
            assert runs == []

            # Creating straight into signed_up also fires the hook (chat path).
            r2 = client.post("/cos/activities/track", headers=auth, json={
                "user_id": uid, "name": "Camp Galileo", "status": "signed_up",
                "price_amount": 500.0,
            })
            aid2 = r2.json()["id"]
            todos2 = [t for t in server.storage_backend.list_todos(uid)
                      if t.get("activity_id") == aid2]
            assert any(t["kind"] == "payment" for t in todos2)
    finally:
        server.storage_backend = prev


# ── Typed materialize to-dos ─────────────────────────────────────────

def test_materialize_types_pay_and_form_todos(store):
    from app.ingest.extract import ExtractedActivity, materialize

    uid = "life-user3"
    artifact_id = store.insert_ingest_artifact(
        user_id=uid, source="paste", media_type="text", raw_text="camp email")
    extracted = ExtractedActivity(
        provider="Rock Camp", activity_name="Rock Camp",
        amount_due=200.0, payment_due_date="2026-06-01",
        forms_required=["medical release"], action_items=["bring a water bottle"],
    )
    made = materialize(store, uid, artifact_id, extracted, kids=[])
    todos = {t["title"]: t["kind"] for t in store.list_todos(uid)
             if t["id"] in made["todo_ids"]}
    assert todos["Pay $200 by 2026-06-01"] == "payment"
    assert todos["Submit form: medical release"] == "form"
    assert todos["bring a water bottle"] == "action"


# ── No-drift + chat-parity guards ────────────────────────────────────

def test_grouping_sites_import_lifecycle():
    """The three old hardcoded groupings must source from lifecycle.py."""
    from app.cos import planning
    from app.email_sync import sync
    assert planning._UNDECIDED_STATUSES is lifecycle.UNDECIDED
    assert sync._REGISTERED is lifecycle.WATCHED
    export_src = (BACKEND_ROOT / "app/cos/export.py").read_text()
    assert "COMMITTED" in export_src


def test_chat_agent_knows_planned():
    """The hub is chat-first — the agent must speak the same lifecycle.

    The planning half of the prompt moved to app/cos/prompt.py when the coach
    and Chief-of-Staff merged into one agent (app/agent.py); app/cos/agent.py
    is now a shim.
    """
    prompt_src = (BACKEND_ROOT / "app/cos/prompt.py").read_text()
    tools_src = (BACKEND_ROOT / "app/cos/tools.py").read_text()
    assert '"planned"' in prompt_src
    assert "planned" in tools_src


def test_on_enter_watched_trip_seeds_prep_todos_idempotently(store):
    # Phase 6: a booked trip seeds its registry-declared prep extras —
    # packing (action), travel consent (form), meds & documents (action) —
    # alongside the payment todo, and never double-seeds.
    uid = "life-user-trip"
    aid = store.track_activity(uid, name="Tahoe", status="planned",
                               activity_type="trip", price_amount=900.0)
    activity = store.get_tracked_activity(aid)

    lifecycle.on_enter_watched(store, uid, activity)
    todos = [t for t in store.list_todos(uid) if t.get("activity_id") == aid]
    titles = {t["title"] for t in todos}
    assert "Make the packing list for Tahoe" in titles
    assert "Travel consent letter for Tahoe" in titles
    assert "Meds & documents for Tahoe" in titles
    consent = next(t for t in todos if "consent" in t["title"].lower())
    assert consent["kind"] == "form"
    assert sorted(t["kind"] for t in todos) == [
        "action", "action", "action", "form", "payment",
    ]  # 2 extras actions + forward-confirmation action

    lifecycle.on_enter_watched(store, uid, activity)
    again = [t for t in store.list_todos(uid) if t.get("activity_id") == aid]
    assert len(again) == len(todos)
