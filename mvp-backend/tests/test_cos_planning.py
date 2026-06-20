"""
Unit tests for the pure Chief-of-Staff planning logic (app/cos/planning.py):
cost tallying, age-eligibility checks, calendar/recurring time-conflict
detection, caregiver coverage gaps, uncovered-week detection, and the composed
dashboard summary. Fully hermetic — no I/O, DB, or network.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cos.planning import (  # noqa: E402
    build_plan_summary,
    check_eligibility,
    cost_summary,
    coverage_gaps,
    detect_time_conflicts,
    uncovered_weeks,
)


def test_cost_summary_mixes_confirmed_tbd_none_and_declined():
    tracked = [
        {"name": "Soccer", "price_amount": 100.0, "price_status": "confirmed",
         "status": "confirmed", "kid_name": "Ceiba"},
        {"name": "Art", "price_amount": 50.0, "price_status": "confirmed",
         "status": "confirmed", "kid_name": "Alkina"},
        {"name": "Swim", "price_amount": 80.0, "price_status": "tbd",
         "status": "interested", "kid_name": "Ceiba"},
        {"name": "Music", "price_amount": None, "price_status": "confirmed",
         "status": "interested", "kid_name": "Ceiba"},
        {"name": "Skipped", "price_amount": 999.0, "price_status": "confirmed",
         "status": "declined", "kid_name": "Ceiba"},
    ]
    out = cost_summary(tracked)

    assert out["confirmed_total"] == 150.0  # 100 + 50; declined excluded
    assert out["tbd_count"] == 2  # tbd Swim + None-priced Music
    assert out["item_count"] == 4  # declined dropped
    assert out["by_kid"]["Ceiba"] == 100.0
    assert out["by_kid"]["Alkina"] == 50.0


def test_check_eligibility_under_in_over_and_none_bounds():
    activity = {"name": "Sailing", "age_min": 5, "age_max": 8}

    under = check_eligibility(activity, {"name": "Alkina", "age": 4})
    assert under["eligible"] is False
    assert "Alkina" in under["reason"]

    in_range = check_eligibility(activity, {"name": "Ceiba", "age": 6})
    assert in_range["eligible"] is True

    over = check_eligibility(activity, {"name": "Rhea", "age": 10})
    assert over["eligible"] is False
    assert "tops out" in over["reason"]

    no_bounds = check_eligibility(
        {"name": "Open", "age_min": None, "age_max": None},
        {"name": "Kai", "age": 3},
    )
    assert no_bounds["eligible"] is True
    assert "no age constraints" in no_bounds["reason"]


def test_detect_time_conflicts_camp_vs_therapy_on_monday():
    # 2026-06-22 is a Monday (weekday 0).
    calendar = [
        {"id": "c1", "title": "Adventure Camp", "kid_name": "Ceiba",
         "start_ts": "2026-06-22T13:00:00", "end_ts": "2026-06-22T16:00:00",
         "kind": "camp"},
    ]
    recurring = [
        {"id": "r1", "title": "OT Therapy", "kid_name": "Ceiba",
         "weekday": 0, "start_time": "13:15", "end_time": "13:45"},
    ]
    conflicts = detect_time_conflicts(calendar, recurring)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c["kid_name"] == "Ceiba"
    assert c["calendar_entry_id"] == "c1"
    assert c["recurring_id"] == "r1"
    assert c["weekday"] == 0


def test_detect_time_conflicts_no_overlap():
    calendar = [
        {"id": "c1", "title": "Adventure Camp", "kid_name": "Ceiba",
         "start_ts": "2026-06-22T13:00:00", "end_ts": "2026-06-22T16:00:00",
         "kind": "camp"},
    ]
    # Same Monday, but therapy is in the morning — no overlap.
    recurring = [
        {"id": "r1", "title": "OT Therapy", "kid_name": "Ceiba",
         "weekday": 0, "start_time": "09:00", "end_time": "09:30"},
    ]
    assert detect_time_conflicts(calendar, recurring) == []


def test_coverage_gaps_flags_gap_and_unassigned_only():
    logistics = [
        {"id": "l1", "week_start": "2026-06-22", "kid_name": "Ceiba",
         "task": "pickup", "caregiver_id": None, "status": "gap"},
        {"id": "l2", "week_start": "2026-06-22", "kid_name": "Alkina",
         "task": "dropoff", "caregiver_id": None, "status": "tbd"},
        {"id": "l3", "week_start": "2026-06-22", "kid_name": "Ceiba",
         "task": "transport", "caregiver_id": "cg1", "status": "assigned"},
    ]
    gaps = coverage_gaps(logistics)
    assert len(gaps) == 2
    ids = {g["id"] for g in gaps}
    assert ids == {"l1", "l2"}
    reasons = {g["id"]: g["reason"] for g in gaps}
    assert reasons["l1"] == "explicitly flagged as a gap"
    assert reasons["l2"] == "no caregiver assigned"


def test_uncovered_weeks_finds_unenrolled_week():
    weeks = ["2026-06-22", "2026-06-29"]
    kids = [{"name": "Ceiba"}]
    calendar = [
        {"week_start": "2026-06-22", "kind": "camp", "kid_name": "Ceiba"},
    ]
    out = uncovered_weeks(calendar, weeks, kids)
    assert out == [{"kid_name": "Ceiba", "week_start": "2026-06-29"}]


def test_build_plan_summary_returns_all_keys():
    tracked = [
        {"name": "Camp", "price_amount": 100.0, "price_status": "confirmed",
         "status": "pending_eligibility", "kid_name": "Ceiba"},
    ]
    calendar = [
        {"id": "c1", "title": "Camp", "kid_name": "Ceiba",
         "start_ts": "2026-06-22T13:00:00", "end_ts": "2026-06-22T16:00:00",
         "week_start": "2026-06-22", "kind": "camp"},
    ]
    recurring = [
        {"id": "r1", "title": "OT", "kid_name": "Ceiba",
         "weekday": 0, "start_time": "13:15", "end_time": "13:45"},
    ]
    logistics = [
        {"id": "l1", "week_start": "2026-06-22", "kid_name": "Ceiba",
         "task": "pickup", "caregiver_id": None, "status": "gap"},
    ]
    kids = [{"name": "Ceiba"}]
    weeks = ["2026-06-22", "2026-06-29"]

    summary = build_plan_summary(
        tracked=tracked,
        calendar_entries=calendar,
        recurring=recurring,
        logistics=logistics,
        kids=kids,
        weeks=weeks,
    )
    assert set(summary.keys()) == {
        "cost",
        "conflicts",
        "coverage_gaps",
        "uncovered_weeks",
        "pending_eligibility",
    }
    assert len(summary["pending_eligibility"]) == 1
    assert len(summary["conflicts"]) == 1
