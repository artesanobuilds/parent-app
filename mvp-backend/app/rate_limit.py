"""
Tiny in-memory rate limiter. Token bucket per (user_id, endpoint_class).
Two classes: 'chat' and 'config'. Replace with Redis when we go multi-replica.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from fastapi import HTTPException


# Tunables via env. Defaults are conservative for closed beta.
CHAT_RATE_PER_MIN = int(os.getenv("RATE_LIMIT_CHAT_PER_MIN", "60"))
CONFIG_RATE_PER_MIN = int(os.getenv("RATE_LIMIT_CONFIG_PER_MIN", "30"))
# Token issuance is unauthenticated and a token-flooding amplifier; cap hard.
# Default aligned to the documented prod value (60/IP/hr, see root CLAUDE.md)
# so code and docs don't drift; tests bump it higher via conftest.
AUTH_RATE_PER_HOUR = int(os.getenv("RATE_LIMIT_AUTH_PER_HOUR", "60"))
# A research run fans out web searches + LLM calls and is expensive; cap per-hour.
RESEARCH_RATE_PER_HOUR = int(os.getenv("RATE_LIMIT_RESEARCH_PER_HOUR", "20"))
# Parent-to-parent DMs: enough for a lively conversation, hostile to spam.
MESSAGE_RATE_PER_MIN = int(os.getenv("RATE_LIMIT_MESSAGE_PER_MIN", "30"))
# First-run agent warm-up: one per parent per onboarding, plus headroom for
# retries/reinstalls. Each run costs an LLM call, so it gets its own bucket
# rather than sharing (and starving) the discovery one.
WARMUP_RATE_PER_HOUR = int(os.getenv("RATE_LIMIT_WARMUP_PER_HOUR", "10"))
# Pre-account onboarding extraction is UNAUTHENTICATED (anon session token) and
# each call is a multimodal LLM invocation — the hardest bucket to leave open.
# Enforced per anon-session AND per IP; a funnel run needs only a handful.
EXTRACT_RATE_PER_HOUR = int(os.getenv("RATE_LIMIT_EXTRACT_PER_HOUR", "30"))


@dataclass
class _Bucket:
    capacity: float
    tokens: float
    refill_per_sec: float
    last_refill: float


class _RateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, str], _Bucket] = {}

    def _bucket_for(self, user_id: str, klass: str) -> _Bucket:
        key = (user_id, klass)
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                if klass == "chat":
                    cap = CHAT_RATE_PER_MIN
                    refill_per_sec = cap / 60.0
                elif klass == "config":
                    cap = CONFIG_RATE_PER_MIN
                    refill_per_sec = cap / 60.0
                elif klass == "auth":
                    cap = AUTH_RATE_PER_HOUR
                    refill_per_sec = cap / 3600.0
                elif klass == "research":
                    cap = RESEARCH_RATE_PER_HOUR
                    refill_per_sec = cap / 3600.0
                elif klass == "message":
                    cap = MESSAGE_RATE_PER_MIN
                    refill_per_sec = cap / 60.0
                elif klass == "warmup":
                    cap = WARMUP_RATE_PER_HOUR
                    refill_per_sec = cap / 3600.0
                elif klass == "extract":
                    cap = EXTRACT_RATE_PER_HOUR
                    refill_per_sec = cap / 3600.0
                else:
                    cap = 60
                    refill_per_sec = 1.0
                b = _Bucket(
                    capacity=cap, tokens=cap,
                    refill_per_sec=refill_per_sec, last_refill=time.monotonic(),
                )
                self._buckets[key] = b
        return b

    def consume(self, user_id: str, klass: str, cost: float = 1.0) -> tuple[bool, float]:
        """
        Try to consume `cost` tokens. Returns (allowed, retry_after_seconds).
        retry_after is meaningful only when allowed=False.
        """
        b = self._bucket_for(user_id, klass)
        with self._lock:
            now = time.monotonic()
            elapsed = now - b.last_refill
            b.tokens = min(b.capacity, b.tokens + elapsed * b.refill_per_sec)
            b.last_refill = now
            if b.tokens >= cost:
                b.tokens -= cost
                return True, 0.0
            deficit = cost - b.tokens
            retry = deficit / b.refill_per_sec if b.refill_per_sec > 0 else 60.0
            return False, retry


_limiter = _RateLimiter()


def enforce(user_id: str, klass: str) -> None:
    """Raise 429 with Retry-After if the user has exhausted their bucket."""
    allowed, retry = _limiter.consume(user_id, klass)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit exceeded for {klass}",
            headers={"Retry-After": str(int(retry) + 1)},
        )
