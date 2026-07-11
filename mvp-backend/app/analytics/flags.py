"""Feature-flag facade (PostHog). ~30 lines, deliberately not OpenFeature:
one dev, three surfaces — a thin wrapper is the escape hatch.

Resolution order: env override `FLAG_<KEY>` (kill switch without a deploy) →
PostHog local evaluation → default. Fails safe to `default` on any error, and
is a pure `default` passthrough when analytics is disabled (no POSTHOG_API_KEY).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _env_override(key: str) -> bool | None:
    raw = os.getenv(f"FLAG_{key.upper().replace('-', '_')}")
    if raw is None:
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def is_enabled(key: str, user_id: str | None = None, *, default: bool = False) -> bool:
    override = _env_override(key)
    if override is not None:
        return override
    from app.analytics import _client, _distinct_id_for
    if _client is None:
        return default
    try:
        distinct_id = _distinct_id_for(user_id) if user_id else "anonymous"
        result = _client.feature_enabled(key, distinct_id, only_evaluate_locally=True)
        return default if result is None else bool(result)
    except Exception:
        logger.debug("[analytics] flag %s eval failed; using default", key, exc_info=True)
        return default
