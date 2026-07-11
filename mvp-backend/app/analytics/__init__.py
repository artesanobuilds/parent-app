"""Product analytics + feature flags (PostHog).

Env-gated exactly like app/observability: with no POSTHOG_API_KEY set, the SDK
is never imported and every function is a no-op, so the app behaves exactly as
before (local / tests / CI are hermetic — no network, no data leaves).

Privacy posture for a kids/family app:
  - distinct_id is the account's OPAQUE `analytics_id`, never the user_id (which
    may be a name) and never PII. If an account has no analytics_id, the event
    is dropped rather than risk sending a raw id.
  - Only allowlisted events + property keys are sent (see events.py); a denylist
    blocks PII-ish keys unconditionally.
  - Autocapture / session replay are OFF (server-side SDK doesn't do them; the
    clients are configured with them disabled).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.analytics import events as _events
from app.analytics.flags import is_enabled  # re-export

logger = logging.getLogger(__name__)

_client: Any = None  # posthog.Posthog | None
# Raise on unknown/denylisted events when set (tests use it to catch mistakes).
_STRICT = os.getenv("ANALYTICS_STRICT", "0").lower() in ("1", "true", "yes")

__all__ = ["init_analytics", "capture", "identify", "is_enabled", "shutdown"]


def init_analytics() -> bool:
    """Initialize the PostHog client. No-op (returns False) without POSTHOG_API_KEY.
    Idempotent — a second call with a live client is a no-op (avoids spawning
    competing background queues)."""
    global _client
    if _client is not None:
        return True
    key = os.getenv("POSTHOG_API_KEY")
    if not key:
        return False
    try:
        from posthog import Posthog  # lazy: only imported when enabled
    except ImportError:
        logger.warning("[analytics] posthog not installed; analytics disabled")
        return False
    _client = Posthog(
        project_api_key=key,
        host=os.getenv("POSTHOG_HOST", "https://us.i.posthog.com"),
        personal_api_key=os.getenv("POSTHOG_PERSONAL_API_KEY") or None,
        # Local flag evaluation (no per-check network hop) + background sends.
        poll_interval=30,
    )
    logger.info("[analytics] PostHog enabled")
    return True


def _distinct_id_for(user_id: str) -> Optional[str]:
    """The account's opaque analytics_id — never the raw user_id."""
    try:
        from app.server import storage_backend
        return storage_backend.analytics_id_for(user_id)
    except Exception:
        return None


def capture(event: str, user_id: str, properties: Optional[dict] = None) -> None:
    """Record a product event. No-op when analytics is disabled. Drops the event
    (never raises in prod) if the account has no analytics_id, so PII can't leak."""
    if event not in _events.EVENTS:
        if _STRICT:
            raise KeyError(f"unknown analytics event: {event!r} (add it to events.EVENTS)")
        logger.debug("[analytics] dropping unknown event %r", event)
        return
    if _client is None:
        return
    distinct_id = _distinct_id_for(user_id)
    if not distinct_id:
        logger.debug("[analytics] no analytics_id for user; dropping %r", event)
        return
    try:
        _client.capture(
            distinct_id=distinct_id,
            event=event,
            properties=_events.sanitize(event, properties),
        )
    except Exception:
        logger.debug("[analytics] capture failed for %r", event, exc_info=True)


def identify(user_id: str, properties: Optional[dict] = None) -> None:
    """Attach coarse, non-PII properties to the opaque analytics id."""
    if _client is None:
        return
    distinct_id = _distinct_id_for(user_id)
    if not distinct_id:
        return
    try:
        _client.identify(distinct_id=distinct_id, properties=properties or {})
    except Exception:
        logger.debug("[analytics] identify failed", exc_info=True)


def shutdown() -> None:
    """Flush queued events on app shutdown."""
    if _client is not None:
        try:
            _client.flush()
        except Exception:
            pass
