"""Crisis-lock push notifications (APNs), env-gated + fire-and-forget.

When a kid companion is crisis-locked we want to alert the parent so they can
review — a lock that no one sees is a safety gap. This sends an APNs push
("[Kid]'s companion was paused — tap to review") to the parent's registered
devices.

Design mirrors the rest of the stack:
- **Env-gated** like `app/observability` — a complete no-op until the APNS_*
  env vars are set (so local/tests/prod-before-setup are unaffected).
- **Fire-and-forget** like `telemetry._post_slack` — dispatched on a daemon
  thread, every exception swallowed; a push failure never affects the request
  or the crisis handling.
- **No new heavy dependency** — token-based APNs signs an ES256 JWT with the
  already-present `cryptography` and POSTs over HTTP/2 with the already-present
  `httpx` (+ `h2`). No `aioapns`/`apns2`.

Config (all required to turn it on):
  APNS_KEY_ID      – the 10-char key id of your APNs auth key (.p8)
  APNS_TEAM_ID     – your Apple Developer team id
  APNS_BUNDLE_ID   – the app bundle id (used as the apns-topic), e.g. MVP.MVParent
  APNS_AUTH_KEY    – the .p8 private key PEM (contents, newlines ok)
Optional:
  APNS_USE_SANDBOX – "true" to hit api.sandbox.push.apple.com (dev builds);
                     default is production (api.push.apple.com — TestFlight/App Store).
"""
from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

_PROD_HOST = "https://api.push.apple.com"
_SANDBOX_HOST = "https://api.sandbox.push.apple.com"

_apns_on = False
_key_id = ""
_team_id = ""
_bundle_id = ""
_auth_key_pem = ""
_host = _PROD_HOST

# Cached provider JWT (valid ~1h; Apple rejects tokens older than 1h and
# refuses regenerating faster than every ~20min, so cache and refresh at ~50min).
_jwt_cache: Optional[str] = None
_jwt_made_at: float = 0.0
_jwt_lock = threading.Lock()


def init_push() -> bool:
    """Enable APNs if fully configured. Called once at server startup (mirrors
    observability.init_*). Returns True when armed."""
    global _apns_on, _key_id, _team_id, _bundle_id, _auth_key_pem, _host
    key_id = os.getenv("APNS_KEY_ID")
    team_id = os.getenv("APNS_TEAM_ID")
    bundle_id = os.getenv("APNS_BUNDLE_ID")
    # The .p8 can be supplied inline (APNS_AUTH_KEY, the PEM contents — used on
    # Railway) or as a file path (APNS_AUTH_KEY_FILE — convenient for local dev,
    # points at the repo's gitignored secrets/ copy so the key is never pasted).
    auth_key = os.getenv("APNS_AUTH_KEY")
    if not auth_key:
        key_path = os.getenv("APNS_AUTH_KEY_FILE")
        if key_path:
            try:
                with open(key_path, "r") as fh:
                    auth_key = fh.read()
            except OSError as exc:
                logger.warning("[push] APNS_AUTH_KEY_FILE=%s unreadable: %s", key_path, exc)
                return False
    if not (key_id and team_id and bundle_id and auth_key):
        return False
    try:
        import httpx  # noqa: F401 — confirm the HTTP/2 client is importable
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        load_pem_private_key(_normalize_pem(auth_key).encode(), password=None)
    except Exception as exc:  # misconfig must not crash boot
        logger.warning("[push] APNS_* set but unusable (%s); push disabled", exc)
        return False
    _key_id, _team_id, _bundle_id = key_id, team_id, bundle_id
    _auth_key_pem = _normalize_pem(auth_key)
    _host = _SANDBOX_HOST if os.getenv("APNS_USE_SANDBOX", "").lower() == "true" else _PROD_HOST
    _apns_on = True
    logger.info("[push] APNs enabled (host=%s topic=%s)", _host, _bundle_id)
    return True


def is_enabled() -> bool:
    return _apns_on


def _normalize_pem(raw: str) -> str:
    # Railway env values can arrive with literal "\n" instead of newlines.
    return raw.replace("\\n", "\n").strip()


def _provider_jwt() -> str:
    global _jwt_cache, _jwt_made_at
    with _jwt_lock:
        if _jwt_cache and (time.time() - _jwt_made_at) < 3000:  # < 50 min
            return _jwt_cache
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        def b64url(b: bytes) -> bytes:
            return base64.urlsafe_b64encode(b).rstrip(b"=")

        header = {"alg": "ES256", "kid": _key_id}
        claims = {"iss": _team_id, "iat": int(time.time())}
        signing_input = (
            b64url(json.dumps(header, separators=(",", ":")).encode())
            + b"." + b64url(json.dumps(claims, separators=(",", ":")).encode())
        )
        key = load_pem_private_key(_auth_key_pem.encode(), password=None)
        der = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = asym_utils.decode_dss_signature(der)
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")  # APNs wants raw r||s, not DER
        _jwt_cache = (signing_input + b"." + b64url(raw_sig)).decode()
        _jwt_made_at = time.time()
        return _jwt_cache


def send_crisis_push(*, storage: Any, user_id: str, kid_name: str, agent_id: str) -> None:
    """Notify the parent that a companion was paused for safety. No-op when APNs
    is unconfigured. Fire-and-forget: dispatched on a daemon thread, never raises."""
    if not _apns_on:
        return
    threading.Thread(
        target=_send_blocking,
        kwargs={"storage": storage, "user_id": user_id, "kid_name": kid_name, "agent_id": agent_id},
        daemon=True,
    ).start()


def _send_blocking(*, storage: Any, user_id: str, kid_name: str, agent_id: str) -> None:
    try:
        tokens: List[str] = storage.list_push_tokens(user_id)
    except Exception as exc:
        logger.warning("[push] could not load device tokens for %s: %s", user_id, exc)
        return
    if not tokens:
        return
    payload = json.dumps({
        "aps": {
            "alert": {
                "title": f"{kid_name}'s companion was paused",
                "body": "A message was flagged by the safety filter. Tap to review.",
            },
            "sound": "default",
            "interruption-level": "time-sensitive",
        },
        "type": "crisis_lock",
        "kid_name": kid_name,
        "agent_id": agent_id,
    }).encode()
    try:
        import httpx
        jwt = _provider_jwt()
        headers = {
            "authorization": f"bearer {jwt}",
            "apns-topic": _bundle_id,
            "apns-push-type": "alert",
            "apns-priority": "10",
        }
        with httpx.Client(http2=True, timeout=5.0) as client:
            for token in tokens:
                try:
                    resp = client.post(f"{_host}/3/device/{token}", content=payload, headers=headers)
                    if resp.status_code == 410:  # device unregistered — prune
                        try:
                            storage.delete_push_token(token)
                        except Exception:
                            pass
                    elif resp.status_code >= 300:
                        logger.warning("[push] APNs %s for a token: %s", resp.status_code, resp.text[:160])
                except Exception as exc:
                    logger.warning("[push] send failed for a token: %s", exc)
    except Exception as exc:
        logger.warning("[push] crisis push failed: %s", exc)
