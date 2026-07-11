"""
v0 closed-beta auth: opaque session tokens (UUID), persisted, validated on
every protected endpoint via FastAPI dependency.

This is intentionally simple. v1 public launch upgrades to Apple Sign-In
(see docs/roadmap.md). The principal-engineer critique was that user_id
arrived in the request body and CORS was wide open — both addressed here.

Usage in FastAPI:
    from app.auth import current_user, authorize_user_match
    @app.post("/some-endpoint")
    def my_endpoint(req: SomeRequest, user_id: str = Depends(current_user)):
        authorize_user_match(authenticated=user_id, claimed=req.user_id)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import jwt
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

# ── JWT access tokens (Phase 2) ──────────────────────────────────────────────
# Short-lived signed access tokens verified in-process (no DB hit). A JWT is
# distinguishable from a legacy opaque token by its two dots. HS256 is right
# here: one service signs and verifies; a future Logto migration replaces this
# wholesale, so asymmetric keys buy nothing.
_JWT_ALG = "HS256"
_ACCESS_TTL_SECONDS = int(os.getenv("AUTH_ACCESS_TTL_MIN", "30")) * 60


def _jwt_secret() -> str:
    secret = os.getenv("AUTH_JWT_SECRET", "").strip()
    if secret:
        return secret
    # Deterministic INSECURE dev fallback so local/test signing round-trips.
    # Prod MUST set AUTH_JWT_SECRET (guarded by tests + startup log).
    logger.warning("[auth] AUTH_JWT_SECRET not set — using an INSECURE dev secret.")
    return "parent-app-dev-jwt-secret-do-not-use-in-prod"


def mint_access_token(user_id: str, *, family_id: Optional[str] = None) -> tuple[str, int]:
    """Return (jwt, expires_in_seconds) for user_id."""
    import uuid
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + _ACCESS_TTL_SECONDS,
        "jti": uuid.uuid4().hex,
    }
    if family_id:
        payload["sid"] = family_id
    return jwt.encode(payload, _jwt_secret(), algorithm=_JWT_ALG), _ACCESS_TTL_SECONDS


def _decode_access_token(token: str) -> Optional[str]:
    """Return the sub (user_id) for a valid JWT, else None."""
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


def _legacy_tokens_enabled() -> bool:
    return os.getenv("AUTH_LEGACY_TOKENS_ENABLED", "1").lower() in ("1", "true", "yes")


def issue_token(user_id: str) -> str:
    """Issue a fresh opaque token for user_id."""
    from app.server import storage_backend
    return storage_backend.issue_auth_token(user_id)


def revoke_token(token: str) -> None:
    from app.server import storage_backend
    storage_backend.revoke_auth_token(token)


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def current_user(authorization: Optional[str] = Header(default=None)) -> str:
    """
    FastAPI dependency. Resolves the Authorization header to a user_id, or
    raises 401 if missing/invalid/revoked.
    """
    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # A JWT has two dots; try to verify it in-process first (no DB hit). This
    # is the Phase 2 access-token path. Anything else falls through to the
    # legacy opaque-token lookup, kept alive during the migration window.
    if token.count(".") == 2:
        user_id = _decode_access_token(token)
        if user_id is not None:
            return user_id
    if _legacy_tokens_enabled():
        from app.server import storage_backend
        user_id = storage_backend.lookup_auth_token(token)
        if user_id is not None:
            return user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or revoked token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authorize_user_match(*, authenticated: str, claimed: str, resource: bool = False) -> None:
    """
    Reject a request whose body/path user_id doesn't match the bearer token's
    user_id. Defense-in-depth against one user reading another user's data.

    Pass resource=True when `claimed` is the owner of a FETCHED ROW (an
    activity, calendar entry, research run, ...): a 403 there would confirm to
    a non-owner that the id exists, so the mismatch must present as 404 —
    indistinguishable from the row not existing at all.
    """
    if authenticated != claimed:
        logger.warning(
            "[auth] user mismatch: token=%s claimed=%s",
            authenticated, claimed,
        )
        if resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id mismatch",
        )
