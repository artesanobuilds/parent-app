"""Operator (CMS) authentication — shared by server.py and the /cms/* routers.

Two ways to authenticate an admin request:
  1. `X-Admin-Token` header carrying ADMIN_TOKEN — for curl/scripts/CI.
  2. An `admin_session` cookie minted by POST /admin/session — for the CMS SPA.
     The browser never sees ADMIN_TOKEN beyond the login form; the cookie is
     HttpOnly + SameSite=Strict, Fernet-encrypted, TTL-bound, and bound to a
     fingerprint of the current ADMIN_TOKEN so rotating the token invalidates
     every outstanding session.

This replaces the old scheme where the CMS baked VITE_ADMIN_TOKEN into its
JS bundle at build time (any CMS visitor could read the operator secret from
the served assets).

Cookie-authenticated requests must also send `X-Requested-With: cms` — with
SameSite=Strict this is belt-and-braces CSRF protection (a cross-site form
can set neither).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel

from app.integrations.crypto import fernet

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-auth"])

ADMIN_SESSION_COOKIE = "admin_session"
# 12h sessions; enforced server-side via Fernet TTL and client-side via Max-Age.
ADMIN_SESSION_TTL_SECONDS = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", str(12 * 3600)))


def _expected_token() -> str:
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="admin endpoints disabled (ADMIN_TOKEN not set)")
    return expected


def _token_fingerprint(token: str) -> str:
    """Non-reversible binder baked into the session payload. Rotating
    ADMIN_TOKEN changes the fingerprint and kills all outstanding sessions."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _session_cookie_valid(request: Request) -> bool:
    cookie = request.cookies.get(ADMIN_SESSION_COOKIE)
    if not cookie:
        return False
    # CSRF belt-and-braces: the CMS client always sends this; cross-site
    # form posts and top-level navigations cannot.
    if request.headers.get("x-requested-with") != "cms":
        return False
    try:
        payload = fernet().decrypt(cookie.encode("ascii"), ttl=ADMIN_SESSION_TTL_SECONDS)
    except Exception:
        return False
    try:
        expected = _expected_token()
    except HTTPException:
        return False
    return hmac.compare_digest(payload.decode("utf-8"), f"admin:{_token_fingerprint(expected)}")


def require_admin_token(
    request: Request,
    x_admin_token: Optional[str] = Header(default=None),
) -> None:
    """
    Operator-only gate for data export / CMS mutation endpoints. These serve or
    mutate the FULL dataset, so per-user auth (current_user) is insufficient.
    Accepts the ADMIN_TOKEN header (scripts) or a valid session cookie (CMS SPA).
    Fails closed when ADMIN_TOKEN is unset.
    """
    expected = _expected_token()
    if x_admin_token and hmac.compare_digest(x_admin_token, expected):
        return
    if _session_cookie_valid(request):
        return
    raise HTTPException(status_code=401, detail="invalid or missing admin credentials")


class AdminSessionRequest(BaseModel):
    token: str


def _client_ip(request: Request) -> str:
    # Mirrors server.client_ip_for (kept local to avoid an import cycle).
    if os.getenv("TRUST_PROXY", "0").lower() in ("1", "true", "yes"):
        first = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


@router.post("/admin/session")
def create_admin_session(req: AdminSessionRequest, request: Request, response: Response):
    """Exchange ADMIN_TOKEN for an HttpOnly session cookie (CMS login)."""
    from app.rate_limit import enforce as rate_limit_enforce
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    expected = _expected_token()
    if not req.token or not hmac.compare_digest(req.token, expected):
        logger.warning("[admin-auth] failed CMS login from %s", _client_ip(request))
        raise HTTPException(status_code=401, detail="invalid admin token")
    payload = f"admin:{_token_fingerprint(expected)}".encode("utf-8")
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=fernet().encrypt(payload).decode("ascii"),
        max_age=ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        secure=os.getenv("ADMIN_COOKIE_SECURE", "1").lower() in ("1", "true", "yes"),
        samesite="strict",
        path="/",
    )
    return {"ok": True, "expires_in": ADMIN_SESSION_TTL_SECONDS}


@router.delete("/admin/session")
def delete_admin_session(response: Response):
    """CMS logout: clear the session cookie."""
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
    return {"ok": True}
