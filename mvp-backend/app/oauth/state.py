"""Signed, short-lived OAuth `state` tokens.

The callback is unauthenticated (Google calls it), so the `state` round-trip is
how we bind the consent back to the requesting user and block CSRF. We
Fernet-encrypt the payload with the shared integration key and enforce a TTL on
verify — the token is opaque + tamper-evident + expiring.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from cryptography.fernet import InvalidToken

from app.integrations import crypto

STATE_TTL_SECONDS = 600  # 10 minutes to complete consent


def sign_state(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return crypto.fernet().encrypt(raw).decode("ascii")


def verify_state(token: str, *, max_age_seconds: int = STATE_TTL_SECONDS) -> Dict[str, Any]:
    """Decode + validate a state token. Raises ValueError if forged or expired."""
    try:
        raw = crypto.fernet().decrypt(token.encode("ascii"), ttl=max_age_seconds)
    except (InvalidToken, ValueError) as exc:
        raise ValueError("invalid or expired oauth state") from exc
    return json.loads(raw)
