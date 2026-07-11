"""Pure due-time rules for registration windows. No storage, no side effects —
everything here is unit-testable with plain datetimes (the transition-matrix
test in tests/test_watchlist.py walks every timezone/known-unknown case).

The one law: **notify BEFORE the window opens, never after.** Concretely:

- time KNOWN (opens_time_known=True): `day_of` is due from `opens_at − 1h`
  until `opens_at` (a late first notification is a broken promise, not a
  degraded one — after opens_at only the miss detector fires).
- time UNKNOWN: `opens_at` is stored as midnight LOCAL of the opens day; the
  `day_of` notification goes out the EVENING BEFORE at 18:00 local (a "it
  opens tomorrow" heads-up beats a 00:00 buzz or a mid-day maybe-too-late).
- `t_minus_7` is due 7 days before the day_of moment, and stops being due the
  moment day_of takes over (never both in one sweep).
- Failed sends may retry until `opens_effective + GRACE`; after that the
  worker escalates (Sentry) and the miss detector owns it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

T_MINUS_7 = "t_minus_7"
DAY_OF = "day_of"

EVE_BEFORE_HOUR = 18       # 6pm local, the evening before (time-unknown rule)
KNOWN_LEAD = timedelta(hours=1)
T_MINUS_LEAD = timedelta(days=7)
RETRY_GRACE = timedelta(hours=2)


def _zone(tz: Optional[str]):
    from zoneinfo import ZoneInfo
    try:
        return ZoneInfo(tz) if tz else timezone.utc
    except Exception:  # noqa: BLE001 — bad tz name → UTC beats crashing a sweep
        return timezone.utc


def parse_ts(value: Any) -> Optional[datetime]:
    """ISO string / datetime → aware UTC datetime (naive input = UTC)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def opens_effective(window: Dict[str, Any]) -> Optional[datetime]:
    """The moment registration actually opens (UTC): opens_at as stored when
    the time is known, else midnight LOCAL of the opens day."""
    opens = parse_ts(window.get("opens_at"))
    if opens is None:
        return None
    if window.get("opens_time_known"):
        return opens
    local = opens.astimezone(_zone(window.get("tz")))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(timezone.utc)


def day_of_due_at(window: Dict[str, Any]) -> Optional[datetime]:
    opens = opens_effective(window)
    if opens is None:
        return None
    if window.get("opens_time_known"):
        return opens - KNOWN_LEAD
    # Evening before, local: 18:00 on the day preceding the local opens day.
    local_midnight = opens.astimezone(_zone(window.get("tz")))
    eve = (local_midnight - timedelta(days=1)).replace(hour=EVE_BEFORE_HOUR)
    return eve.astimezone(timezone.utc)


def t_minus_due_at(window: Dict[str, Any]) -> Optional[datetime]:
    day_of = day_of_due_at(window)
    return day_of - T_MINUS_LEAD if day_of else None


def retry_deadline(window: Dict[str, Any]) -> Optional[datetime]:
    opens = opens_effective(window)
    return opens + RETRY_GRACE if opens else None


def due_kind(window: Dict[str, Any], now: Optional[datetime] = None) -> Optional[str]:
    """Which notification (if any) is due RIGHT NOW — at most one: day_of wins
    once its window starts (a t_minus_7 landing minutes before day_of would be
    spam, not diligence). None after opens_effective — never notify late."""
    now = now or datetime.now(timezone.utc)
    opens = opens_effective(window)
    day_of = day_of_due_at(window)
    if opens is None or day_of is None:
        return None
    if day_of <= now < opens:
        return DAY_OF
    t7 = day_of - T_MINUS_LEAD
    if t7 <= now < day_of:
        return T_MINUS_7
    return None
