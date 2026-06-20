"""
Lightweight telemetry. v0 ships:
- Slack webhook on every flagged moderation event (severity >= medium).
- Per-flag metrics counters (in-process).

Set SLACK_WEBHOOK_URL to enable Slack delivery; absent = local logging only.
Production target: Datadog / Honeycomb. Captured here behind one interface so
the swap is contained.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from typing import Any, Dict, Literal, Optional

import urllib.request

TTSFallbackReason = Literal["quota", "network", "crisis", "key_missing", "partial_stream"]

logger = logging.getLogger(__name__)


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()


# ── Counters (process-local) ─────────────────────────────────────────

_counter_lock = threading.Lock()
_counters: Dict[str, int] = defaultdict(int)


def incr(metric: str, by: int = 1) -> None:
    with _counter_lock:
        _counters[metric] += by


def snapshot() -> Dict[str, int]:
    with _counter_lock:
        return dict(_counters)


# ── TTS counters ─────────────────────────────────────────────────────


def incr_tts_chars(provider: str, user_id: str, n: int) -> None:
    """Track characters synthesized per provider. provider is 'elevenlabs' or 'system'."""
    if n <= 0:
        return
    incr(f"tts.{provider}.chars", n)
    logger.info("[tts] chars provider=%s user=%s n=%d", provider, user_id, n)


def incr_tts_fallback(reason: TTSFallbackReason, user_id: str) -> None:
    """Track fallback events with a structured reason tag."""
    incr(f"tts.fallback.{reason}")
    logger.info("[tts] fallback reason=%s user=%s", reason, user_id)


# ── Slack alerts ─────────────────────────────────────────────────────


def _post_slack(payload: Dict[str, Any]) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    try:
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status >= 300:
                logger.warning("[telemetry] Slack webhook %s: %s", resp.status, resp.read()[:200])
    except Exception as exc:
        logger.warning("[telemetry] Slack webhook failed: %s", exc)


def alert_moderation_event(
    *,
    user_id: str,
    kid_name: str,
    severity: str,
    category: str,
    action: str,
    excerpt: str,
    agent_id: Optional[str] = None,
) -> None:
    """
    Fire-and-forget Slack alert for a flagged moderation event.

    Privacy note: excerpt should be redacted/short. Full content stays in the
    moderation_events table; Slack just gets a heads-up summary.
    """
    incr(f"moderation.{severity}.{action}")

    if severity == "low":
        return
    if not SLACK_WEBHOOK_URL:
        logger.warning(
            "[alert] severity=%s category=%s action=%s user=%s kid=%s excerpt=%s",
            severity, category, action, user_id, kid_name, excerpt[:100],
        )
        return

    color = {
        "crisis": "#cc0000",
        "high": "#cc6600",
        "medium": "#cccc00",
    }.get(severity, "#888888")

    text = (
        f"*Moderation event* — `{severity}` / `{category}` / `{action}`\n"
        f"user=`{user_id}`  kid=`{kid_name}`  agent=`{agent_id or 'n/a'}`\n"
        f"_{excerpt[:240]}_"
    )
    payload = {
        "attachments": [
            {"color": color, "text": text, "mrkdwn_in": ["text"]},
        ],
    }
    threading.Thread(target=_post_slack, args=(payload,), daemon=True).start()


def alert_crisis(
    *,
    user_id: str,
    kid_name: str,
    excerpt: str,
    agent_id: Optional[str] = None,
) -> None:
    """Higher-priority crisis alert. Same channel for v0; route to pager next."""
    alert_moderation_event(
        user_id=user_id, kid_name=kid_name, severity="crisis",
        category="crisis", action="crisis_routed", excerpt=excerpt,
        agent_id=agent_id,
    )
