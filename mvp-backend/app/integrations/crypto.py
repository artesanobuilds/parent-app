"""Encryption-at-rest for integration refresh tokens (R5).

OAuth refresh tokens are long-lived credentials, so they are Fernet-encrypted
before they touch `integration_accounts.encrypted_refresh_token`. The key comes
from `INTEGRATION_ENC_KEY` (a urlsafe-base64 32-byte Fernet key). In prod that
env var MUST be set; without it a deterministic, clearly-insecure dev key is used
so local/test round-trips work — and a loud warning is logged.

Generate a real key with:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _dev_key() -> bytes:
    """Deterministic, INSECURE key for local/test use only — never for prod."""
    raw = hashlib.sha256(b"parent-app-dev-integration-key").digest()  # 32 bytes
    return base64.urlsafe_b64encode(raw)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    configured = os.getenv("INTEGRATION_ENC_KEY", "").strip()
    if configured:
        try:
            return Fernet(configured.encode())
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "INTEGRATION_ENC_KEY is not a valid Fernet key (urlsafe-base64, "
                "32 bytes). Regenerate with Fernet.generate_key()."
            ) from exc
    logger.warning(
        "[integrations] INTEGRATION_ENC_KEY not set — using an INSECURE dev key. "
        "Set INTEGRATION_ENC_KEY in production before connecting any account."
    )
    return Fernet(_dev_key())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a refresh token → urlsafe ciphertext string."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored token. Raises ValueError on a bad/forged/rotated token."""
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ValueError("could not decrypt integration token") from exc
