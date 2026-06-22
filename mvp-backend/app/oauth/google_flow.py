"""Google OAuth client: build the consent URL + exchange the code.

Thin wrapper over google-auth-oauthlib's Flow, imported lazily so the module
loads without the SDK and tests can monkeypatch these two functions. The live
calls need GOOGLE_OAUTH_CLIENT_ID/SECRET and are untested end-to-end pending a
registered OAuth client + Google verification.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# Per-kind Google scopes. email = restricted (needs verification + CASA).
SCOPE_FOR_KIND = {
    "email": "https://www.googleapis.com/auth/gmail.readonly",
    "calendar": "https://www.googleapis.com/auth/calendar.events",
}
# Always request identity so we can record which account was connected.
BASE_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email"]

_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_TOKEN_URI = "https://oauth2.googleapis.com/token"


@dataclass
class ExchangeResult:
    refresh_token: Optional[str]
    scopes: List[str]
    email: Optional[str]


def is_configured() -> bool:
    return bool(
        os.getenv("GOOGLE_OAUTH_CLIENT_ID") and os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    )


def scopes_for_kinds(kinds: List[str]) -> List[str]:
    return BASE_SCOPES + [SCOPE_FOR_KIND[k] for k in kinds if k in SCOPE_FOR_KIND]


def _client_config(redirect_uri: str) -> dict:
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "auth_uri": _AUTH_URI,
            "token_uri": _TOKEN_URI,
            "redirect_uris": [redirect_uri],
        }
    }


def build_authorization_url(*, scopes: List[str], redirect_uri: str, state: str) -> str:
    from google_auth_oauthlib.flow import Flow  # lazy

    flow = Flow.from_client_config(
        _client_config(redirect_uri), scopes=scopes, redirect_uri=redirect_uri
    )
    url, _ = flow.authorization_url(
        access_type="offline",      # required to receive a refresh token
        include_granted_scopes="true",
        prompt="consent",           # force a refresh token even on re-consent
        state=state,
    )
    return url


def exchange_code(*, code: str, scopes: List[str], redirect_uri: str) -> ExchangeResult:
    from google_auth_oauthlib.flow import Flow  # lazy

    flow = Flow.from_client_config(
        _client_config(redirect_uri), scopes=scopes, redirect_uri=redirect_uri
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    return ExchangeResult(
        refresh_token=getattr(creds, "refresh_token", None),
        scopes=list(getattr(creds, "scopes", None) or scopes),
        email=_email_from_credentials(creds),
    )


def _email_from_credentials(creds) -> Optional[str]:
    """Pull the account email from the id_token if present (best-effort)."""
    id_token = getattr(creds, "id_token", None)
    if not id_token:
        return None
    try:
        import base64
        import json

        payload = id_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # pad base64
        claims = json.loads(base64.urlsafe_b64decode(payload))
        return claims.get("email")
    except Exception:  # noqa: BLE001
        return None
