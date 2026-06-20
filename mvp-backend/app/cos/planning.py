"""Pure planning logic for the Chief-of-Staff feature.

This module reproduces the derived intelligence a parent built by hand in a
kids'-camp coordination spreadsheet: a running cost tally, time-conflict
detection (camp hours vs. recurring therapy), age-eligibility checks, and
caregiver coverage gaps.

Everything here is intentionally PURE: functions take plain lists of dicts
(matching the shapes the storage layer returns) and return plain dicts/lists.
No I/O, no DB, no network, no imports from ``app.*`` — only the stdlib. This
keeps the logic trivially testable and reusable by the agent layer.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any, Optional

__all__ = [
    "cost_summary",
    "check_eligibility",
    "detect_time_conflicts",
    "coverage_gaps",
    "uncovered_weeks",
    "build_plan_summary",
]

_COVERING_KINDS = {"camp", "class", "program"}


def cost_summary(tracked: list[dict]) -> dict:
    """Summarize the cost picture across tracked activities.

    Each ``tracked`` dict may carry: ``name``, ``price_amount`` (float|None),
    ``price_status`` ("confirmed"|"tbd"), ``status`` (e.g. "confirmed",
    "pending_eligibility", "interested", "declined"), ``kid_name``.

    Items with ``status == "declined"`` are excluded entirely. Returns:
    ``{"confirmed_total", "tbd_count", "item_count", "lines", "by_kid"}``
    where ``confirmed_total`` sums ``price_amount`` for confirmed-priced items,
    ``tbd_count`` counts items whose price is not confirmed or is missing, and
    ``by_kid`` maps each kid to their confirmed subtotal.
    """
    lines: list[dict] = []
    by_kid: dict[str, float] = {}
    confirmed_total = 0.0
    tbd_count = 0

    for item in tracked or []:
        if (item.get("status") or "") == "declined":
            continue

        name = item.get("name")
        kid_name = item.get("kid_name")
        price_amount = item.get("price_amount")
        price_status = item.get("price_status")

        is_confirmed = price_status == "confirmed" and price_amount is not None

        if is_confirmed:
            amount = float(price_amount)
            confirmed_total += amount
            if kid_name is not None:
                by_kid[kid_name] = by_kid.get(kid_name, 0.0) + amount
            else:
                by_kid.setdefault(kid_name, 0.0)
        else:
            tbd_count += 1
            # Ensure the kid shows up in by_kid even with a zero confirmed subtotal.
            by_kid.setdefault(kid_name, 0.0)

        lines.append(
            {
                "name": name,
                "kid_name": kid_name,
                "price_amount": price_amount,
                "price_status": price_status,
            }
        )

    return {
        "confirmed_total": confirmed_total,
        "tbd_count": tbd_count,
        "item_count": len(lines),
        "lines": lines,
        "by_kid": by_kid,
    }


def check_eligibility(activity: dict, kid: dict) -> dict:
    """Check whether ``kid`` falls inside an activity's age window.

    ``activity`` may carry ``age_min`` (float|None), ``age_max`` (float|None),
    ``name``. ``kid`` may carry ``name`` and ``age`` (float|None).

    Returns ``{"eligible": bool, "reason": str}``. When the kid's age is unknown
    or the activity declares no bounds, the result is eligible-by-default.
    """
    activity = activity or {}
    kid = kid or {}

    name = activity.get("name") or "this activity"
    kid_name = kid.get("name") or "Kid"
    age = kid.get("age")
    age_min = activity.get("age_min")
    age_max = activity.get("age_max")

    if age is None or (age_min is None and age_max is None):
        return {"eligible": True, "reason": "no age constraints to check"}

    if age_min is not None and age < age_min:
        return {
            "eligible": False,
            "reason": f"{kid_name} is {_fmt_num(age)}; {name} starts at {_fmt_num(age_min)}",
        }

    if age_max is not None and age > age_max:
        return {
            "eligible": False,
            "reason": f"{kid_name} is {_fmt_num(age)}; {name} tops out at {_fmt_num(age_max)}",
        }

    lo = _fmt_num(age_min) if age_min is not None else "?"
    hi = _fmt_num(age_max) if age_max is not None else "?"
    return {
        "eligible": True,
        "reason": f"{kid_name} ({_fmt_num(age)}) fits {lo}-{hi}",
    }


def detect_time_conflicts(
    calendar_entries: list[dict], recurring: list[dict]
) -> list[dict]:
    """Detect per-kid clashes between recurring appointments and calendar entries.

    ``calendar_entries`` carry: ``id``, ``title``, ``kid_name``, ``start_ts``
    (ISO str|None), ``end_ts`` (ISO str|None), ``kind``. ``recurring`` carry:
    ``id``, ``title``, ``kid_name``, ``weekday`` (0=Mon..6=Sun, int|None),
    ``start_time`` ("HH:MM"|None), ``end_time`` ("HH:MM"|None).

    A conflict exists when a recurring appointment's weekday matches a calendar
    entry's weekday (derived from ``start_ts``) and their times-of-day overlap
    (``start_a < end_b and start_b < end_a``). Only same-kid pairs are compared;
    a ``kid_name`` of None or "both" matches any kid. Entries missing the data
    needed to compare are skipped.

    Returns a list of conflict dicts describing each clash.
    """
    conflicts: list[dict] = []

    for entry in calendar_entries or []:
        start_dt = _parse_iso(entry.get("start_ts"))
        end_dt = _parse_iso(entry.get("end_ts"))
        if start_dt is None or end_dt is None:
            continue

        entry_weekday = start_dt.weekday()
        entry_start_t = start_dt.time()
        entry_end_t = end_dt.time()
        entry_kid = entry.get("kid_name")

        for appt in recurring or []:
            weekday = appt.get("weekday")
            if weekday is None or weekday != entry_weekday:
                continue
            if not _kids_match(entry_kid, appt.get("kid_name")):
                continue

            appt_start_t = _parse_hhmm(appt.get("start_time"))
            appt_end_t = _parse_hhmm(appt.get("end_time"))
            if appt_start_t is None or appt_end_t is None:
                continue

            # Overlap on time-of-day: start_a < end_b and start_b < end_a.
            if entry_start_t < appt_end_t and appt_start_t < entry_end_t:
                conflicts.append(
                    {
                        "kid_name": _resolve_kid(entry_kid, appt.get("kid_name")),
                        "calendar_entry_id": entry.get("id"),
                        "calendar_title": entry.get("title"),
                        "recurring_id": appt.get("id"),
                        "recurring_title": appt.get("title"),
                        "weekday": entry_weekday,
                        "detail": (
                            f"{entry.get('title')} "
                            f"({_fmt_time(entry_start_t)}-{_fmt_time(entry_end_t)}) "
                            f"overlaps {appt.get('title')} "
                            f"({_fmt_time(appt_start_t)}-{_fmt_time(appt_end_t)}) "
                            f"on {_weekday_name(entry_weekday)}"
                        ),
                    }
                )

    return conflicts


def coverage_gaps(logistics: list[dict]) -> list[dict]:
    """Surface logistics rows that lack caregiver coverage.

    ``logistics`` dicts carry: ``id``, ``week_start`` (ISO date str|None),
    ``kid_name``, ``task`` ("dropoff"|"pickup"|"transport"|"attend"),
    ``caregiver_id`` (str|None), ``status`` ("assigned"|"gap"|"tbd").

    A row is a gap when ``status == "gap"`` OR (``status != "assigned"`` and no
    caregiver is assigned). Returns the gap rows with a human ``reason``.
    """
    gaps: list[dict] = []

    for row in logistics or []:
        status = row.get("status")
        caregiver_id = row.get("caregiver_id")

        explicit_gap = status == "gap"
        unassigned = status != "assigned" and caregiver_id is None

        if not (explicit_gap or unassigned):
            continue

        reason = (
            "explicitly flagged as a gap"
            if explicit_gap
            else "no caregiver assigned"
        )

        gaps.append(
            {
                "id": row.get("id"),
                "week_start": row.get("week_start"),
                "kid_name": row.get("kid_name"),
                "task": row.get("task"),
                "status": status,
                "reason": reason,
            }
        )

    return gaps


def uncovered_weeks(
    calendar_entries: list[dict], weeks: list[str], kids: list[dict]
) -> list[dict]:
    """Find kid/week combos with no camp/class/program coverage.

    ``weeks`` is a list of ISO week-start date strings the parent cares about;
    ``kids`` is ``[{"name", ...}]``. ``calendar_entries`` carry ``week_start``
    (ISO date str), ``kind``, ``kid_name``. Entries with ``kind`` in
    {"camp", "class", "program"} count as covering.

    Returns ``[{"kid_name", "week_start"}]`` for every kid/week pair that has no
    covering entry.
    """
    # Build a set of (kid_name, week_start) that are covered.
    covered: set[tuple[Optional[str], Optional[str]]] = set()
    for entry in calendar_entries or []:
        if (entry.get("kind") or "") in _COVERING_KINDS:
            covered.add((entry.get("kid_name"), entry.get("week_start")))

    result: list[dict] = []
    for kid in kids or []:
        kid_name = kid.get("name")
        for week_start in weeks or []:
            if (kid_name, week_start) in covered:
                continue
            result.append({"kid_name": kid_name, "week_start": week_start})

    return result


def build_plan_summary(
    *,
    tracked: list[dict],
    calendar_entries: list[dict],
    recurring: list[dict],
    logistics: list[dict],
    kids: list[dict],
    weeks: Optional[list[str]] = None,
) -> dict:
    """Compose all planning views into one dashboard payload.

    Returns a dict with keys ``cost``, ``conflicts``, ``coverage_gaps``,
    ``uncovered_weeks``, and ``pending_eligibility`` (the tracked items still
    awaiting an age-eligibility decision).
    """
    return {
        "cost": cost_summary(tracked),
        "conflicts": detect_time_conflicts(calendar_entries, recurring),
        "coverage_gaps": coverage_gaps(logistics),
        "uncovered_weeks": uncovered_weeks(calendar_entries, weeks or [], kids),
        "pending_eligibility": [
            t for t in (tracked or []) if t.get("status") == "pending_eligibility"
        ],
    }


# --------------------------------------------------------------------------- #
# Internal helpers (pure, stdlib-only)
# --------------------------------------------------------------------------- #

_WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _fmt_num(value: Any) -> str:
    """Render a number without a trailing ``.0`` for whole values."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if f.is_integer():
        return str(int(f))
    return str(f)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp string, tolerating a trailing ``Z``."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_hhmm(value: Optional[str]) -> Optional[time]:
    """Parse an ``HH:MM`` (optionally ``HH:MM:SS``) string into a ``time``."""
    if not value or not isinstance(value, str):
        return None
    parts = value.strip().split(":")
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour, minute, second)
    except (ValueError, IndexError):
        return None


def _fmt_time(t: time) -> str:
    """Render a ``time`` as ``HH:MM``."""
    return f"{t.hour:02d}:{t.minute:02d}"


def _weekday_name(weekday: int) -> str:
    if 0 <= weekday <= 6:
        return _WEEKDAY_NAMES[weekday]
    return f"weekday {weekday}"


def _kids_match(a: Optional[str], b: Optional[str]) -> bool:
    """Whether two kid_name values refer to the same kid.

    A value of None or "both" is treated as a wildcard that matches anyone.
    """
    if _is_wildcard(a) or _is_wildcard(b):
        return True
    return a == b


def _is_wildcard(name: Optional[str]) -> bool:
    return name is None or (isinstance(name, str) and name.lower() == "both")


def _resolve_kid(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Pick the most specific kid_name from a matched pair."""
    if not _is_wildcard(a):
        return a
    if not _is_wildcard(b):
        return b
    return a
