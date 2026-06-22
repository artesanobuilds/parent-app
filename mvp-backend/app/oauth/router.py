"""Google OAuth endpoints: connect / callback / status / disconnect.

Flow (iOS ASWebAuthenticationSession):
  1. App → GET /oauth/google/authorize-url?kinds=email,calendar  (authenticated)
     → { authorization_url }
  2. App opens it; user consents; Google → GET /oauth/google/callback?code&state
     (unauthenticated — Google calls it; bound to the user via the signed state)
  3. Backend exchanges the code, stores the encrypted refresh token in
     integration_accounts (one row per kind), then 302s to the app's custom
     scheme (mvparent://oauth/google?status=...).
Plus GET /oauth/google/status and POST /oauth/google/disconnect for the UI.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth import current_user, authorize_user_match
from app.integrations.crypto import encrypt_token
from app.oauth import google_flow, state as oauth_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth/google", tags=["oauth"])

_DEFAULT_REDIRECT = (
    "https://mvp-backend-production-8678.up.railway.app/oauth/google/callback"
)


def _storage():
    from app.server import storage_backend

    return storage_backend


def _redirect_uri() -> str:
    return os.getenv("GOOGLE_OAUTH_REDIRECT_URI", _DEFAULT_REDIRECT)


def _app_scheme() -> str:
    return os.getenv("APP_OAUTH_CALLBACK_SCHEME", "mvparent")


def _app_redirect(status: str, **params: str) -> RedirectResponse:
    """302 to the app's custom scheme so ASWebAuthenticationSession closes."""
    query = "&".join(f"{k}={quote(v)}" for k, v in {"status": status, **params}.items() if v)
    return RedirectResponse(url=f"{_app_scheme()}://oauth/google?{query}")


def _parse_kinds(kinds: str) -> List[str]:
    valid = [k.strip() for k in kinds.split(",") if k.strip() in google_flow.SCOPE_FOR_KIND]
    # de-dup, preserve order
    seen: List[str] = []
    for k in valid:
        if k not in seen:
            seen.append(k)
    return seen


class AuthorizeURLResponse(BaseModel):
    authorization_url: str


@router.get("/authorize-url", response_model=AuthorizeURLResponse)
def authorize_url(kinds: str = "email,calendar", user_id: str = Depends(current_user)):
    if not google_flow.is_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    kind_list = _parse_kinds(kinds)
    if not kind_list:
        raise HTTPException(status_code=400, detail="no valid kinds (email|calendar)")

    state = oauth_state.sign_state({"user_id": user_id, "kinds": kind_list})
    url = google_flow.build_authorization_url(
        scopes=google_flow.scopes_for_kinds(kind_list),
        redirect_uri=_redirect_uri(),
        state=state,
    )
    return AuthorizeURLResponse(authorization_url=url)


@router.get("/callback")
def callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    # Google bounces here. Everything funnels back to the app via the scheme.
    if error:
        return _app_redirect("error", reason=error)
    if not code or not state:
        return _app_redirect("error", reason="missing_code")
    try:
        data = oauth_state.verify_state(state)
        user_id = data["user_id"]
        kinds = data["kinds"]
    except (ValueError, KeyError):
        return _app_redirect("error", reason="bad_state")

    try:
        result = google_flow.exchange_code(
            code=code,
            scopes=google_flow.scopes_for_kinds(kinds),
            redirect_uri=_redirect_uri(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[oauth/google] code exchange failed: %s", exc)
        return _app_redirect("error", reason="exchange_failed")

    if not result.refresh_token:
        # No refresh token = the user previously consented and Google withheld
        # one. prompt=consent should prevent this, but guard anyway.
        return _app_redirect("error", reason="no_refresh_token")

    enc = encrypt_token(result.refresh_token)
    storage = _storage()
    for kind in kinds:
        storage.upsert_integration_account(
            user_id,
            provider="google",
            kind=kind,
            encrypted_refresh_token=enc,
            account_email=result.email,
            scopes=" ".join(google_flow.scopes_for_kinds([kind])),
        )
    return _app_redirect("success", provider="google", email=result.email or "")


@router.get("/status")
def status(user_id: str = Depends(current_user)):
    """Connected accounts for the Settings UI. Never returns the token."""
    accounts = _storage().list_integration_accounts(user_id)
    return {
        "configured": google_flow.is_configured(),
        "accounts": [
            {
                "provider": a["provider"],
                "kind": a["kind"],
                "account_email": a["account_email"],
                "status": a["status"],
                "connected_at": a["connected_at"],
                "last_sync_at": a["last_sync_at"],
            }
            for a in accounts
            if a["provider"] == "google"
        ],
    }


class DisconnectRequest(BaseModel):
    user_id: str
    kind: str  # email | calendar


@router.post("/disconnect")
def disconnect(body: DisconnectRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    if body.kind not in google_flow.SCOPE_FOR_KIND:
        raise HTTPException(status_code=400, detail="kind must be email|calendar")
    _storage().revoke_integration_account(user_id, "google", body.kind)
    return {"ok": True}
