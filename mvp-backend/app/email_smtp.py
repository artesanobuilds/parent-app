"""
Dead-simple transactional email via stdlib smtplib.

Used by the /debug/report endpoint to forward test-user diagnostic bundles to
the developer. Intentionally minimal: one plaintext send, STARTTLS, all config
from env. If SMTP isn't configured we log and no-op so the caller never 500s
(a debug report that can't be emailed is still better than a crash).

Env:
  SMTP_HOST        e.g. smtp.gmail.com
  SMTP_PORT        default 587 (STARTTLS)
  SMTP_USER        login user (often == SMTP_FROM)
  SMTP_PASSWORD    app password (for Gmail/Workspace, a 16-char app password)
  SMTP_FROM        From: address; defaults to SMTP_USER
  DEBUG_REPORT_TO  recipient; defaults to miguel@miguelalvarado.com
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

DEFAULT_REPORT_TO = "miguel@miguelalvarado.com"


def _config() -> dict | None:
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    if not host or not user or not password:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "from": os.getenv("SMTP_FROM", "").strip() or user,
    }


def report_recipient() -> str:
    return os.getenv("DEBUG_REPORT_TO", "").strip() or DEFAULT_REPORT_TO


def send_email(subject: str, body: str, to: str | None = None) -> bool:
    """
    Send a plaintext email. Returns True on success, False if SMTP isn't
    configured or the send fails. Never raises — callers treat email as
    best-effort.
    """
    cfg = _config()
    if cfg is None:
        logger.warning("[email] SMTP not configured; skipping send: %r", subject)
        return False

    recipient = (to or report_recipient()).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from"]
    msg["To"] = recipient
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as smtp:
            smtp.starttls()
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
        logger.info("[email] sent %r to %s", subject, recipient)
        return True
    except Exception as e:  # noqa: BLE001 - best-effort; log and move on
        logger.error("[email] send failed: %s", e)
        return False
