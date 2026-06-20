"""
Unit tests for the Chief-of-Staff storage CRUD layer (duckdb_storage.py):
tracked_activities, calendar_entries, recurring_appointments, caregivers,
logistics_assignments, todo_items, and cos_messages. Covers create -> list/get,
update mutation, delete (where applicable), JSON round-trips, status filtering,
and week_start filtering. Hermetic — a tempfile DuckDB, no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return DuckDBStorage(db_path=tmp_path / "cos.duckdb")


def test_tracked_activities_crud_json_and_status_filter(store):
    a1 = store.track_activity(
        "u1",
        name="Soccer Camp",
        kid_name="Ceiba",
        week_start="2026-06-22",
        contact={"phone": "555-1212", "name": "Coach"},
        details={"price": 200},
    )
    store.track_activity("u1", name="Art Class", status="signed_up")

    got = store.get_tracked_activity(a1)
    assert got["name"] == "Soccer Camp"
    assert got["status"] == "exploring"  # R1: default landing bucket
    # JSON round-trips under clean keys.
    assert got["contact"] == {"phone": "555-1212", "name": "Coach"}
    assert got["details"] == {"price": 200}
    # Date serialised to ISO string.
    assert got["week_start"] == "2026-06-22"

    all_acts = store.list_tracked_activities("u1")
    assert len(all_acts) == 2

    # status filtering.
    signed = store.list_tracked_activities("u1", status="signed_up")
    assert len(signed) == 1 and signed[0]["name"] == "Art Class"

    # update mutates a scalar field and a JSON field (mapped contact->contact_json).
    store.update_tracked_activity(a1, status="confirmed", contact={"phone": "999"})
    after = store.get_tracked_activity(a1)
    assert after["status"] == "confirmed"
    assert after["contact"] == {"phone": "999"}


def test_calendar_entries_crud_and_week_filter(store):
    e1 = store.add_calendar_entry(
        "u1", title="Camp Mon", kid_name="Ceiba", week_start="2026-06-22",
        start_ts="2026-06-22T09:00:00+00:00",
    )
    store.add_calendar_entry("u1", title="Other week", week_start="2026-06-29")

    got = store.get_calendar_entry(e1)
    assert got["title"] == "Camp Mon"
    assert got["week_start"] == "2026-06-22"

    # week_start filter.
    wk = store.list_calendar_entries("u1", week_start="2026-06-22")
    assert len(wk) == 1 and wk[0]["title"] == "Camp Mon"

    # kid_name filter.
    by_kid = store.list_calendar_entries("u1", kid_name="Ceiba")
    assert len(by_kid) == 1

    store.update_calendar_entry(e1, status="pending", title="Camp Mon AM")
    assert store.get_calendar_entry(e1)["status"] == "pending"
    assert store.get_calendar_entry(e1)["title"] == "Camp Mon AM"

    store.delete_calendar_entry(e1)
    assert store.get_calendar_entry(e1) is None
    assert len(store.list_calendar_entries("u1")) == 1


def test_recurring_appointments_crud(store):
    appt = store.add_recurring_appointment(
        "u1", title="Therapy", kid_name="Ceiba", weekday=2,
        start_time="15:00", active_from="2026-01-01",
    )
    appts = store.list_recurring_appointments("u1")
    assert len(appts) == 1
    assert appts[0]["title"] == "Therapy"
    assert appts[0]["weekday"] == 2
    assert appts[0]["active_from"] == "2026-01-01"

    store.delete_recurring_appointment(appt)
    assert store.list_recurring_appointments("u1") == []


def test_caregivers_crud_json_roundtrip(store):
    cg = store.add_caregiver(
        "u1", name="Nanny Pat", role="nanny",
        contact={"phone": "555-0000"},
        default_availability={"mon": "all-day"},
    )
    caregivers = store.list_caregivers("u1")
    assert len(caregivers) == 1
    c = caregivers[0]
    assert c["name"] == "Nanny Pat"
    # JSON columns exposed under clean keys, parsed to dicts.
    assert c["contact"] == {"phone": "555-0000"}
    assert c["default_availability"] == {"mon": "all-day"}

    store.update_caregiver(cg, role="family_friend", contact={"phone": "555-1111"})
    after = store.list_caregivers("u1")[0]
    assert after["role"] == "family_friend"
    assert after["contact"] == {"phone": "555-1111"}


def test_logistics_assignments_crud_and_week_filter(store):
    cg = store.add_caregiver("u1", name="Pat")
    asg = store.add_logistics_assignment(
        "u1", task="pickup", week_start="2026-06-22", kid_name="Ceiba",
    )
    store.add_logistics_assignment("u1", task="dropoff", week_start="2026-06-29")

    wk = store.list_logistics_assignments("u1", week_start="2026-06-22")
    assert len(wk) == 1 and wk[0]["task"] == "pickup"
    assert wk[0]["week_start"] == "2026-06-22"
    assert len(store.list_logistics_assignments("u1")) == 2

    store.update_logistics_assignment(asg, status="assigned", caregiver_id=cg)
    updated = store.list_logistics_assignments("u1", week_start="2026-06-22")[0]
    assert updated["status"] == "assigned"
    assert updated["caregiver_id"] == cg


def test_todos_crud_and_status_filter(store):
    t1 = store.add_todo("u1", title="Pay deposit", kind="payment", due_date="2026-06-20")
    store.add_todo("u1", title="Done thing", status="done")

    open_todos = store.list_todos("u1", status="open")
    assert len(open_todos) == 1 and open_todos[0]["title"] == "Pay deposit"
    assert open_todos[0]["due_date"] == "2026-06-20"

    assert len(store.list_todos("u1")) == 2

    store.update_todo(t1, status="done", detail="paid via venmo")
    assert store.list_todos("u1", status="done")
    refreshed = [t for t in store.list_todos("u1") if t["id"] == t1][0]
    assert refreshed["status"] == "done"
    assert refreshed["detail"] == "paid via venmo"


def test_cos_messages_append_and_ordering(store):
    store.append_cos_message("u1", role="user", content="hello")
    store.append_cos_message("u1", role="assistant", content="hi there")
    store.append_cos_message("u1", thread_id="other", role="user", content="elsewhere")

    msgs = store.get_cos_messages("u1")
    assert [m["content"] for m in msgs] == ["hello", "hi there"]
    assert msgs[0]["role"] == "user" and msgs[1]["role"] == "assistant"
    assert msgs[0]["created_at"] is not None

    other = store.get_cos_messages("u1", thread_id="other")
    assert len(other) == 1 and other[0]["content"] == "elsewhere"
