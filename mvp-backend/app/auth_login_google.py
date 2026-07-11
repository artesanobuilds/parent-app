"""Sign-in-with-Google via web redirect (Phase 2).

The iOS app opens /auth/google/start in ASWebAuthenticationSession; the web
dashboard navigates to it. It 302s to Google's consent, Google 302s back to the
already-registered /oauth/google/callback, which (seeing login=true in the
signed state) calls complete_google_login here: exchange the code, verify the
returned id_token against Google's JWKS, find-or-create the account, and hand
back a ONE-TIME login code the client swaps for a token pair via
/auth/exchange-code. The code (not the tokens) rides the redirect so tokens
never land in a URL/referrer/history.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional
from urllib.parse import quote

from fastapi.responses import RedirectResponse

from app import auth_providers
from app.integrations import crypto
from app.oauth import google_flow, state as oauth_state

logger = logging.getLogger(__name__)

LOGIN_CODE_TTL_SECONDS = 60

# Single-use enforcement for login codes. One container in prod, so an in-memory
# set is sufficient; entries self-expire via the Fernet TTL regardless.
_consumed_jti: set[str] = set()


def _app_scheme() -> str:
    return os.getenv("APP_OAUTH_CALLBACK_SCHEME", "mvparent")


def _dashboard_base() -> str:
    # Where the web dashboard is served (same origin as the API in prod).
    return os.getenv("PUBLIC_BASE_URL", "").rstrip("/")


def _redirect_uri() -> str:
    from app.oauth.router import _redirect_uri as ru
    return ru()


def mint_login_code(*, provider: str, provider_sub: str, email, email_verified: bool) -> str:
    """Mint a one-time code carrying the VERIFIED identity (not a user_id).
    Account resolution/claiming is deferred to /auth/exchange-code so the Google
    web flow can claim a legacy account just like native /auth/login — the app
    supplies the legacy proof on the exchange call."""
    payload = {
        "provider": provider, "sub": provider_sub,
        "email": email, "email_verified": email_verified,
        "jti": uuid.uuid4().hex, "t": int(time.time()),
    }
    return crypto.fernet().encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")


def redeem_login_code(code: str) -> Optional[Dict[str, Any]]:
    """Return the verified-identity dict for a valid, unexpired, unused code;
    else None. Consumes the code (single use)."""
    try:
        raw = crypto.fernet().decrypt(code.encode("ascii"), ttl=LOGIN_CODE_TTL_SECONDS)
    except Exception:
        return None
    try:
        payload = json.loads(raw)
        jti = payload["jti"]
        if not payload.get("sub") or not payload.get("provider"):
            return None
    except (ValueError, KeyError):
        return None
    if jti in _consumed_jti:
        return None
    _consumed_jti.add(jti)
    return payload


def build_start_url(surface: str) -> str:
    """Google consent URL for a login (openid/email/profile only)."""
    code_verifier = google_flow.generate_code_verifier()
    signed = oauth_state.sign_state(
        {"login": True, "surface": surface, "cv": code_verifier}
    )
    return google_flow.build_authorization_url(
        scopes=google_flow.LOGIN_SCOPES,
        redirect_uri=_redirect_uri(),
        state=signed,
        code_verifier=code_verifier,
        include_granted_scopes=False,   # login asks for ONLY openid+email
        access_type="online",           # no refresh token needed for login
        prompt="select_account",        # pick account; don't force scope re-consent
    )


def _bounce(surface: str, **params: str) -> RedirectResponse:
    """Send the browser back to the app (custom scheme) or dashboard (fragment)."""
    query = "&".join(f"{k}={quote(v)}" for k, v in params.items() if v)
    if surface == "dashboard":
        base = _dashboard_base() or ""
        return RedirectResponse(url=f"{base}/dashboard/#{query}")
    return RedirectResponse(url=f"{_app_scheme()}://auth?{query}")


def complete_google_login(state_data: Dict[str, Any], code: str) -> RedirectResponse:
    surface = state_data.get("surface", "ios")
    code_verifier = state_data.get("cv")
    if not code_verifier:
        return _bounce(surface, status="error", reason="bad_state")

    try:
        result = google_flow.exchange_code(
            code=code,
            scopes=google_flow.LOGIN_SCOPES,
            redirect_uri=_redirect_uri(),
            code_verifier=code_verifier,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[auth/google] login code exchange failed: %s", exc)
        return _bounce(surface, status="error", reason="exchange_failed")

    if not result.id_token:
        return _bounce(surface, status="error", reason="no_id_token")

    try:
        provider_sub, email, email_verified = auth_providers.verify_google(result.id_token)
    except auth_providers.ProviderVerificationError as exc:
        logger.warning("[auth/google] id_token verification failed: %s", exc)
        return _bounce(surface, status="error", reason="bad_id_token")

    # DEFER account creation to /auth/exchange-code — the code carries only the
    # verified identity, so the exchange (with the app's legacy proof) can claim
    # an existing account instead of always creating a fresh one.
    code_out = mint_login_code(
        provider="google", provider_sub=provider_sub,
        email=email, email_verified=email_verified,
    )
    return _bounce(surface, status="success", login_code=code_out)
