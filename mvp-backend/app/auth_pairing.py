"""Short-lived, single-use pairing codes: sign the web dashboard in from the
phone (Apple-only accounts have no web Apple button).

The iOS app (authenticated) requests a short code; the user types it on the
dashboard within the TTL. In-memory + single container in prod, so a dict is
sufficient; entries carry an expiry and are consumed on use.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, Optional, Tuple

PAIRING_TTL_SECONDS = 600  # 10 minutes

_lock = threading.Lock()
_codes: Dict[str, Tuple[str, float]] = {}  # code -> (user_id, expires_at)


def _reap(now: float) -> None:
    expired = [c for c, (_, exp) in _codes.items() if exp <= now]
    for c in expired:
        _codes.pop(c, None)


def put_pairing(code: str, user_id: str) -> None:
    now = time.time()
    with _lock:
        _reap(now)
        _codes[code] = (user_id, now + PAIRING_TTL_SECONDS)


def take_pairing(code: str) -> Optional[str]:
    """Return the user_id for a valid code and consume it; else None."""
    now = time.time()
    with _lock:
        _reap(now)
        entry = _codes.pop(code.strip().upper() if code else "", None)
    if entry is None:
        return None
    user_id, expires_at = entry
    if expires_at <= now:
        return None
    return user_id
