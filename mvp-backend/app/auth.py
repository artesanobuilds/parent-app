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
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


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
    from app.server import storage_backend
    user_id = storage_backend.lookup_auth_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or revoked token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def authorize_user_match(*, authenticated: str, claimed: str) -> None:
    """
    Reject a request whose body/path user_id doesn't match the bearer token's
    user_id. Defense-in-depth against one user reading another user's data.
    """
    if authenticated != claimed:
        logger.warning(
            "[auth] user mismatch: token=%s claimed=%s",
            authenticated, claimed,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id mismatch",
        )
