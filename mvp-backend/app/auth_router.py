"""Phase 2 auth endpoints: native Sign in with Apple / Google, token refresh,
logout, and legacy-account claiming.

Login flow:
  1. Client obtains a provider id_token (native SIWA / Google Sign-In on iOS;
     the OAuth web redirect on the dashboard).
  2. POST /auth/login {provider, id_token, ...}. We verify the id_token against
     the provider JWKS, find-or-create the account, mint an access JWT + a
     rotating refresh token, and return them.

Legacy claim: an upgraded client that still holds a valid legacy opaque token
sends {legacy_user_id, legacy_token}. If that token is valid for that user_id
AND the user has no identity for this provider yet, we bind the new identity to
the EXISTING user_id — the family keeps all its data under the same key.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth import (
    current_user,
    mint_access_token,
)
from app.admin_auth import require_admin_token as _require_admin
from app import auth_providers
from app.rate_limit import enforce as rate_limit_enforce

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

REFRESH_TTL_DAYS = 60


def _storage():
    from app.server import storage_backend
    return storage_backend


def _client_ip(request: Request) -> str:
    from app.server import client_ip_for
    return client_ip_for(request)


class LoginRequest(BaseModel):
    provider: str            # "apple" | "google"
    id_token: str
    nonce: Optional[str] = None
    platform: Optional[str] = None       # "ios" | "web"
    device_name: Optional[str] = None
    # Migration: an upgraded client proves ownership of its legacy account.
    legacy_user_id: Optional[str] = None
    legacy_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None   # omit → revoke ALL sessions for the user


def resolve_account(
    storage, *, provider: str, provider_sub: str, email, email_verified: bool,
    legacy_user_id=None, legacy_token=None,
) -> tuple[str, bool, bool]:
    """Find-or-create-or-CLAIM an account for a verified provider identity.
    Shared by /auth/login (Apple/Google native) and /auth/exchange-code (Google
    web redirect) so BOTH paths can claim a legacy account. Returns
    (user_id, is_new_account, linked_legacy)."""
    existing = storage.get_identity(provider, provider_sub)
    if existing is not None:
        return existing["user_id"], False, False

    user_id = None
    linked_legacy = False
    if legacy_user_id and legacy_token:
        legacy_owner = storage.lookup_auth_token(legacy_token)
        if legacy_owner == legacy_user_id and not storage.user_has_any_identity(legacy_user_id):
            user_id = legacy_user_id
            linked_legacy = True
            storage.write_audit_event(
                user_id=user_id, actor=user_id, action="auth.legacy_claimed",
                details={"provider": provider},
            )
    is_new_account = False
    if user_id is None:
        import uuid
        user_id = uuid.uuid4().hex
        is_new_account = True
    storage.get_or_create_account(user_id, primary_email=email)
    storage.link_identity(
        user_id=user_id, provider=provider, provider_sub=provider_sub,
        email=email, email_verified=email_verified,
    )
    return user_id, is_new_account, linked_legacy


def _issue_session(storage, user_id: str, *, platform, device_name) -> dict:
    refresh = storage.create_refresh_token(
        user_id=user_id, platform=platform, device_name=device_name,
        ttl_days=REFRESH_TTL_DAYS,
    )
    access, expires_in = mint_access_token(user_id)
    account = storage.get_or_create_account(user_id)
    return {
        "access_token": access,
        "expires_in": expires_in,
        "refresh_token": refresh,
        "user_id": user_id,
        "analytics_id": account["analytics_id"],
        # Client routes on this: has a profile → skip onboarding → main app;
        # no profile → onboarding. Backend is the source of truth, so a
        # returning user on a new device isn't re-onboarded.
        "has_profile": storage.user_has_profile(user_id),
    }


@router.post("/auth/login")
def auth_login(body: LoginRequest, request: Request):
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    storage = _storage()

    try:
        provider_sub, email, email_verified = auth_providers.verify(
            body.provider, body.id_token, nonce=body.nonce,
        )
    except auth_providers.ProviderVerificationError as exc:
        logger.warning("[auth] login verification failed: %s", exc)
        # In prod, keep the reason opaque. When AUTH_DEBUG_ERRORS=1 (local
        # debugging), surface the specific verification failure to the client.
        if os.getenv("AUTH_DEBUG_ERRORS", "0").lower() in ("1", "true", "yes"):
            raise HTTPException(status_code=401, detail=f"invalid id_token: {exc}")
        raise HTTPException(status_code=401, detail="invalid id_token")

    user_id, is_new_account, linked_legacy = resolve_account(
        storage, provider=body.provider, provider_sub=provider_sub,
        email=email, email_verified=email_verified,
        legacy_user_id=body.legacy_user_id, legacy_token=body.legacy_token,
    )

    session = _issue_session(storage, user_id, platform=body.platform, device_name=body.device_name)
    session["is_new_account"] = is_new_account
    session["linked_legacy"] = linked_legacy

    # Analytics (no-op until Phase 3 wires it). Kept behind a lazy import so
    # this module has no hard dependency on the analytics package.
    try:
        from app.analytics import capture as analytics_capture
        analytics_capture(
            "login_succeeded", user_id,
            {"provider": body.provider, "platform": body.platform or "unknown",
             "is_new_account": is_new_account, "linked_legacy": linked_legacy},
        )
    except Exception:
        pass

    return session


@router.post("/auth/refresh")
def auth_refresh(body: RefreshRequest, request: Request):
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    storage = _storage()
    rotated = storage.rotate_refresh_token(body.refresh_token)
    if rotated is None:
        raise HTTPException(status_code=401, detail="invalid or reused refresh token")
    access, expires_in = mint_access_token(rotated["user_id"], family_id=rotated["family_id"])
    return {
        "access_token": access,
        "expires_in": expires_in,
        "refresh_token": rotated["refresh_token"],
        "user_id": rotated["user_id"],
    }


@router.post("/auth/logout")
def auth_logout(body: LogoutRequest, user_id: str = Depends(current_user)):
    storage = _storage()
    if body.refresh_token:
        storage.revoke_refresh_token(body.refresh_token)
    else:
        storage.revoke_all_refresh_tokens(user_id)
    return {"ok": True}


# ── Sign in with Google (web redirect; iOS ASWebAuthenticationSession + web) ──

@router.get("/auth/google/start")
def auth_google_start(surface: str = "ios"):
    """Unauthenticated: 302 to Google consent for a LOGIN (openid/email/profile
    only). The callback mints a one-time login_code the client redeems below."""
    from app.oauth import google_flow
    from app.auth_login_google import build_start_url
    if not google_flow.is_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    if surface not in ("ios", "dashboard"):
        surface = "ios"
    return RedirectResponse(url=build_start_url(surface))


class ExchangeCodeRequest(BaseModel):
    login_code: str
    platform: Optional[str] = None
    device_name: Optional[str] = None
    # Legacy proof so a Google web-redirect login can CLAIM an existing account
    # (same as native /auth/login). Without these, a legacy user signing in with
    # Google would get a fresh account and orphan their family data.
    legacy_user_id: Optional[str] = None
    legacy_token: Optional[str] = None


@router.post("/auth/exchange-code")
def auth_exchange_code(body: ExchangeCodeRequest, request: Request):
    """Swap a one-time login_code (from the Google redirect) for a token pair.
    Resolves/claims the account HERE (not at the redirect) so the app's legacy
    proof can bind the Google identity to an existing account."""
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    from app.auth_login_google import redeem_login_code
    ident = redeem_login_code(body.login_code)
    if ident is None:
        raise HTTPException(status_code=401, detail="invalid or expired login code")
    storage = _storage()
    user_id, is_new_account, linked_legacy = resolve_account(
        storage, provider=ident["provider"], provider_sub=ident["sub"],
        email=ident.get("email"), email_verified=bool(ident.get("email_verified")),
        legacy_user_id=body.legacy_user_id, legacy_token=body.legacy_token,
    )
    session = _issue_session(storage, user_id, platform=body.platform, device_name=body.device_name)
    session["is_new_account"] = is_new_account
    session["linked_legacy"] = linked_legacy
    return session


# ── Pairing code: sign a dashboard session from the phone (Apple-only users) ──

class PairingLoginRequest(BaseModel):
    code: str
    platform: Optional[str] = None
    device_name: Optional[str] = None


@router.post("/auth/pairing-code")
def auth_pairing_code(user_id: str = Depends(current_user)):
    """Authenticated (from the iOS app): mint a short human-typable code the
    user enters on the web dashboard to sign in there without re-authenticating
    with the provider. Useful for Apple-only accounts (no web Apple button)."""
    from app.auth_login_google import mint_login_code
    # Reuse the one-time-code machinery but surface a short handle. We store the
    # full opaque code server-side keyed by a short code the user types.
    import secrets
    from app.auth_pairing import put_pairing
    short = "-".join(secrets.token_hex(2) for _ in range(2)).upper()  # e.g. 3F9A-1C77
    put_pairing(short, user_id)
    return {"code": short, "expires_in": 600}


@router.post("/auth/pairing-login")
def auth_pairing_login(body: PairingLoginRequest, request: Request):
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    from app.auth_pairing import take_pairing
    user_id = take_pairing(body.code)
    if user_id is None:
        raise HTTPException(status_code=401, detail="invalid or expired pairing code")
    session = _issue_session(_storage(), user_id, platform=body.platform or "web", device_name=body.device_name)
    session["is_new_account"] = False
    session["linked_legacy"] = False
    return session


# ── Admin: migration monitoring + manual relink safety net ────────────────────

class RelinkRequest(BaseModel):
    provider: str            # "apple" | "google"
    provider_sub: str        # the sub from the founder's sign-in (see migration-status)
    target_user_id: str      # the legacy user_id whose family data must be preserved


@router.get("/admin/auth/migration-status")
def admin_migration_status(_: None = Depends(_require_admin)):
    """Operator view: which accounts have claimed a sign-in identity, which
    haven't, and every provider identity on file. Use before/after a founder
    signs in to confirm the claim landed on the right account."""
    return _storage().migration_status()


@router.post("/admin/auth/link-legacy")
def admin_link_legacy(body: RelinkRequest, _: None = Depends(_require_admin)):
    """Safety net: bind a provider identity to a legacy user_id, moving it off a
    wrong (fresh, empty) account and deleting that empty account. Fixes a founder
    whose automatic claim failed (expired token / fresh install) and whose Apple/
    Google sub landed on a new blank account instead of their real family."""
    if body.provider not in ("apple", "google"):
        raise HTTPException(status_code=400, detail="provider must be apple|google")
    return _storage().admin_relink_identity(
        provider=body.provider, provider_sub=body.provider_sub,
        target_user_id=body.target_user_id, actor="admin",
    )
