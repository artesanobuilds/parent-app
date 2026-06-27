"""Per-user two-way Google Calendar sync — the unit of work the R4 daemon runs.

Push leg: our owned `calendar_entries` (source != 'gcal') that have a concrete
start and are new or locally edited get created/updated on the parent's Google
Calendar; we stamp the returned event id + synced_at so the next run only pushes
new or changed rows. Pull leg: external events on the parent's calendar are
folded back in as `source='gcal'` rows (kind='external') so the plan — and the
conflict/coverage helpers — see the parent's real commitments. Events we pushed
are skipped on pull (matched by provider_event_id) so we never re-ingest our own
echo. `provider` may be injected for tests.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# How far back/forward the pull leg scans the parent's calendar.
_PULL_BACK_DAYS = 1
_PULL_FORWARD_DAYS = 90


def run_calendar_sync(
    storage: Any,
    user_id: str,
    *,
    provider: Any = None,
    on_progress: Optional[Any] = None,
) -> Dict[str, Any]:
    """Reconcile one user's plan with their Google Calendar in both directions.
    Returns `{pushed, pulled, detail}` where `detail` records per-direction
    items for the CMS run-detail view."""
    detail: Dict[str, Any] = {
        "account_email": None,
        "note": None,
        "pushed_items": [],
        "pulled_items": [],
    }
    acct = storage.get_integration_account(user_id, "google", "calendar")
    if not acct or acct.get("status") != "connected":
        detail["note"] = "no connected Google Calendar account"
        return {"pushed": 0, "pulled": 0, "detail": detail}
    detail["account_email"] = acct.get("account_email")

    if provider is None:
        provider = _build_provider(acct)

    pushed = _push_leg(storage, user_id, provider, detail, on_progress)
    pulled = _pull_leg(storage, user_id, provider, detail)

    storage.mark_integration_synced(acct["id"])
    if pushed == 0 and pulled == 0 and not detail["note"]:
        detail["note"] = "calendar already in sync (nothing to push or pull)"
    return {"pushed": pushed, "pulled": pulled, "detail": detail}


# ── push: our entries → Google ───────────────────────────────────────────────

def _push_leg(
    storage: Any, user_id: str, provider: Any, detail: Dict[str, Any], on_progress
) -> int:
    from app.integrations.base import CalendarEvent

    pushed = 0
    for entry in storage.list_calendar_entries_to_push(user_id):
        ev = CalendarEvent(
            title=entry.get("title") or "(untitled)",
            start=entry.get("start_ts"),
            end=entry.get("end_ts") or entry.get("start_ts"),
            all_day=bool(entry.get("all_day")),
            location=entry.get("location_text"),
            description=_describe(entry),
            provider_event_id=entry.get("provider_event_id"),
        )
        was_update = bool(entry.get("provider_event_id"))
        try:
            event_id = provider.push_event(ev)
            storage.mark_calendar_pushed(entry["id"], event_id)
            pushed += 1
            detail["pushed_items"].append({
                "title": ev.title, "start": ev.start,
                "action": "updated" if was_update else "created",
            })
        except Exception as exc:  # noqa: BLE001 — one bad entry shouldn't abort the run
            logger.warning("[calendar-sync] push failed for %s: %s", entry.get("id"), exc)
            detail["pushed_items"].append({
                "title": ev.title, "action": "push_failed", "error": str(exc)[:200],
            })
        if on_progress:
            try:
                on_progress(pushed)
            except Exception:  # noqa: BLE001
                pass
    return pushed


# ── pull: Google → our entries ───────────────────────────────────────────────

def _pull_leg(storage: Any, user_id: str, provider: Any, detail: Dict[str, Any]) -> int:
    since, until = _pull_window()
    try:
        external = provider.pull_events(since=since, until=until)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[calendar-sync] pull failed for %s: %s", user_id, exc)
        detail["note"] = f"pull failed: {str(exc)[:160]}"
        return 0

    pulled = 0
    for ev in external:
        if not ev.provider_event_id:
            continue
        existing = storage.get_calendar_entry_by_provider_event(user_id, ev.provider_event_id)
        if existing and existing.get("source") != "gcal":
            # An event WE pushed — don't re-ingest our own echo as a new row.
            continue
        if existing:
            storage.update_calendar_entry(
                existing["id"],
                title=ev.title or "(untitled)",
                start_ts=ev.start,
                end_ts=ev.end,
                all_day=ev.all_day,
                location_text=ev.location,
            )
            action = "updated"
        else:
            storage.add_calendar_entry(
                user_id,
                title=ev.title or "(untitled)",
                start_ts=ev.start,
                end_ts=ev.end,
                all_day=ev.all_day,
                location_text=ev.location,
                kind="external",
                status="confirmed",
                source="gcal",
                provider_event_id=ev.provider_event_id,
            )
            action = "imported"
        pulled += 1
        detail["pulled_items"].append({
            "title": ev.title, "start": ev.start, "action": action,
        })
    return pulled


# ── helpers ──────────────────────────────────────────────────────────────────

def _describe(entry: Dict[str, Any]) -> str:
    """A short human description for the Google event body — gives the parent
    context (which kid, what kind, status) on events we created."""
    bits: List[str] = []
    if entry.get("kid_name"):
        bits.append(str(entry["kid_name"]))
    if entry.get("kind"):
        bits.append(str(entry["kind"]))
    if entry.get("status") and entry["status"] != "confirmed":
        bits.append(str(entry["status"]))
    prefix = " · ".join(bits)
    return f"{prefix} — synced from your family plan" if prefix else "Synced from your family plan"


def _pull_window() -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=_PULL_BACK_DAYS)
    until = now + timedelta(days=_PULL_FORWARD_DAYS)
    return since.isoformat(), until.isoformat()


def _build_provider(acct: Dict[str, Any]) -> Any:
    from app.integrations.base import OAuthCredentials
    from app.integrations.crypto import decrypt_token
    from app.integrations.registry import get_calendar_provider

    creds = OAuthCredentials(
        refresh_token=decrypt_token(acct["encrypted_refresh_token"]),
        scopes=(acct.get("scopes") or "").split(),
        account_email=acct.get("account_email"),
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    )
    return get_calendar_provider("google", creds)
