"""Verify Sign in with Apple / Google identity tokens (Phase 2 login).

Both providers issue OIDC id_tokens signed with rotating RSA keys published at
a JWKS endpoint. We verify the signature against the provider's JWKS and check
issuer/audience/expiry, then return the stable subject (`sub`) that keys the
account. The `sub` is what we store in auth_identities — never the email
(which can change and, for Apple private-relay, is per-app).

No secrets here: verification is public-key only. (Apple's *token exchange*
would need the .p8 client-secret JWT, but native Sign in with Apple on iOS
hands us an id_token directly, so we only verify.)
"""
from __future__ import annotations

import hashlib
import logging
import os
import ssl
from typing import Optional, Tuple

import certifi
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS = "https://appleid.apple.com/auth/keys"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
GOOGLE_JWKS = "https://www.googleapis.com/oauth2/v3/certs"

# Verify the JWKS endpoints' TLS against certifi's CA bundle explicitly, rather
# than relying on the host's system cert store being configured. Without this,
# a macOS Python.framework (no linked CA certs) raises CERTIFICATE_VERIFY_FAILED
# when PyJWKClient's urllib fetch hits appleid.apple.com — and any minimal
# container is one `update-ca-certificates` away from the same failure.
_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

# Module-level JWKS clients cache signing keys (with their own TTL) so we don't
# refetch on every login.
_apple_jwks = PyJWKClient(APPLE_JWKS, ssl_context=_ssl_ctx)
_google_jwks = PyJWKClient(GOOGLE_JWKS, ssl_context=_ssl_ctx)


class ProviderVerificationError(Exception):
    """Raised when an id_token fails verification."""


def _apple_audiences() -> list[str]:
    # The iOS app's bundle id is the audience for native Sign in with Apple.
    return [a.strip() for a in os.getenv(
        "APPLE_AUD", os.getenv("APNS_BUNDLE_ID", "MVP.MVParent")
    ).split(",") if a.strip()]


def _google_audiences() -> list[str]:
    # Accept the configured OAuth client id(s). A dedicated iOS login client id
    # can be added via GOOGLE_LOGIN_CLIENT_IDS (comma-separated).
    auds = [a.strip() for a in os.getenv("GOOGLE_LOGIN_CLIENT_IDS", "").split(",") if a.strip()]
    web = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if web:
        auds.append(web)
    return auds


def verify_apple(id_token: str, *, nonce: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    """Verify an Apple id_token. Returns (provider_sub, email, email_verified).

    If `nonce` is supplied it must match the token's nonce claim (Apple stores
    sha256(nonce) when the client sends a raw nonce; we accept either form)."""
    try:
        signing_key = _apple_jwks.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_apple_audiences(),
            issuer=APPLE_ISSUER,
            options={"require": ["exp", "iss", "sub"]},
        )
    except Exception as exc:  # jwt.* + key fetch errors
        raise ProviderVerificationError(f"apple id_token verification failed: {exc}") from exc

    if nonce is not None:
        claim_nonce = claims.get("nonce")
        hashed = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        if claim_nonce not in (nonce, hashed):
            raise ProviderVerificationError("apple id_token nonce mismatch")

    email = claims.get("email")
    email_verified = str(claims.get("email_verified", "false")).lower() == "true"
    return claims["sub"], email, email_verified


def verify_google(id_token: str) -> Tuple[str, Optional[str], bool]:
    """Verify a Google id_token. Returns (provider_sub, email, email_verified)."""
    try:
        signing_key = _google_jwks.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_google_audiences(),
            issuer=list(GOOGLE_ISSUERS),
            options={"require": ["exp", "iss", "sub"]},
        )
    except Exception as exc:
        raise ProviderVerificationError(f"google id_token verification failed: {exc}") from exc

    email = claims.get("email")
    email_verified = bool(claims.get("email_verified", False))
    return claims["sub"], email, email_verified


def verify(provider: str, id_token: str, *, nonce: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    if provider == "apple":
        return verify_apple(id_token, nonce=nonce)
    if provider == "google":
        return verify_google(id_token)
    raise ProviderVerificationError(f"unknown provider: {provider!r}")
