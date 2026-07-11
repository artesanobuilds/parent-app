"""Window creation — the ONE write path for registration windows (tool, HTTP
router, and the lifecycle auto-create hook all call watch_registration).

Date normalization matters here: a date-only opens_at ("2026-08-12") means
"sometime that day, LOCAL" — stored as local midnight with
opens_time_known=False so the due rules notify the evening before. A full
datetime is stored as-is with opens_time_known=True. The family's timezone
comes from their profile ZIP (geo.tz_for_postal).

This is a user-state write under the durable-verified rule: failures RAISE —
the agent tool surfaces them, never swallows ("we're watching it" must be
true the moment it's said).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from app import observability as obs
from app.watchlist import windows as W

logger = logging.getLogger(__name__)

_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _family_tz(user_id: str) -> str:
    from app.profiling import profiling_service
    from app.research.geo import tz_for_postal

    try:
        profile = profiling_service.get_family_profile(user_id) or {}
        postal = (profile.get("parent") or {}).get("postal_code")
    except Exception:  # noqa: BLE001
        postal = None
    return tz_for_postal(postal)


def watch_registration(
    storage: Any,
    user_id: str,
    *,
    opens_at: str,
    activity_id: Optional[str] = None,
    provider: Optional[str] = None,
    signup_url: Optional[str] = None,
    closes_at: Optional[str] = None,
    source: str = "manual",
    confidence: Optional[str] = None,
    metro: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a watching window and return it. Raises on any failure."""
    tz = _family_tz(user_id)

    raw = (opens_at or "").strip()
    if _DATE_ONLY.match(raw):
        # Date-only: local midnight of that day; due rules notify the evening
        # before. NEVER store bare UTC midnight — that shifts the local day.
        from zoneinfo import ZoneInfo
        local = datetime.fromisoformat(raw).replace(tzinfo=ZoneInfo(tz))
        opens_dt = local
        opens_time_known = False
    else:
        opens_dt = W.parse_ts(raw)
        if opens_dt is None:
            raise ValueError(
                f"opens_at must be an ISO date or datetime, got {opens_at!r}"
            )
        opens_time_known = True

    # Trust design: agent-researched dates are never "confirmed" — their T-7
    # nudge asks the parent to confirm (one tap → confirmed).
    if confidence is None:
        confidence = "estimated" if source == "agent_research" else "confirmed"
    if source == "agent_research":
        confidence = "estimated"

    window_id = storage.create_registration_window(
        user_id,
        activity_id=activity_id,
        provider=provider,
        signup_url=signup_url,
        opens_at=opens_dt.isoformat(),
        tz=tz,
        opens_time_known=opens_time_known,
        closes_at=closes_at,
        source=source,
        confidence=confidence,
        metro=metro,
    )
    window = storage.get_registration_window(window_id)
    if not window:  # durable-verified: the write must be readable back
        raise RuntimeError("registration window write could not be verified")

    obs.count("watchlist.windows.created", source=source, confidence=confidence)
    try:
        from app.analytics import capture
        capture("registration_window_watched", user_id,
                {"source": source, "confidence": confidence})
    except Exception:  # noqa: BLE001
        pass

    # Wake the worker so a window created inside its due band notifies within
    # seconds, not at the next poll.
    try:
        from app.watchlist.worker import watchlist_worker
        if watchlist_worker is not None:
            watchlist_worker.notify()
    except Exception:  # noqa: BLE001
        pass

    return window


def maybe_watch_from_activity(storage: Any, user_id: str, activity: Dict[str, Any]) -> None:
    """Auto-create a window when a registration_watch-capable activity carries
    a known open date (details.registration_opens_at — set by ingest/agent).
    Best-effort + idempotent (one window per activity); called from lifecycle.
    Never raises."""
    try:
        from app.cos.verticals import get_profile

        if not get_profile(activity.get("activity_type")).registration_watch:
            return
        opens = (activity.get("details") or {}).get("registration_opens_at")
        if not opens:
            return
        existing = [w for w in storage.list_registration_windows(user_id)
                    if w.get("activity_id") == activity.get("id")
                    and w.get("status") == "watching"]
        if existing:
            return
        watch_registration(
            storage, user_id,
            opens_at=str(opens),
            activity_id=activity.get("id"),
            provider=activity.get("provider"),
            signup_url=activity.get("signup_url"),
            source="agent_research",
        )
    except Exception:  # noqa: BLE001 — a nicety, never breaks the mutation
        logger.exception("[watchlist] auto-create from activity failed")
        obs.count("cos.lifecycle.hook_error", hook="watch_from_activity")
